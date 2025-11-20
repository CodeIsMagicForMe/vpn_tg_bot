import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

import httpx
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, BufferedInputFile, CallbackQuery, Message

from .config import get_settings
# Explicit import from the concrete keyboards module avoids cases where
# partial package imports leave helpers unavailable at runtime (seen as
# NameError in docker logs).
from .keyboards.main_kb import get_buy_menu, get_main_menu, get_profile_menu

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = Router()


@dataclass
class Subscription:
    user_id: int
    tariff_code: str
    active_until: datetime
    proto: str = "amneziawg"
    node_id: str = "default_nl"

    @property
    def is_active(self) -> bool:
        return self.active_until > datetime.utcnow()


TARIFFS: Dict[str, Dict[str, str | int]] = {
    "trial": {"name": "Trial", "duration": 3, "price": 0},
    "light": {"name": "Light", "duration": 30, "price": 110},
    "family": {"name": "Family", "duration": 30, "price": 200},
    "unlimited": {"name": "Unlimited", "duration": 30, "price": 290},
    "year": {"name": "Годовая", "duration": 365, "price": 290 * 12 * 0.65},
}

SUBSCRIPTIONS: Dict[int, Subscription] = {}


def _get_active_subscription(user_id: int) -> Optional[Subscription]:
    sub = SUBSCRIPTIONS.get(user_id)
    if sub and sub.is_active:
        return sub
    return None


def _create_subscription(user_id: int, tariff_code: str) -> Subscription:
    tariff = TARIFFS.get(tariff_code, TARIFFS["trial"])
    duration_days = int(tariff.get("duration", 3))
    sub = Subscription(
        user_id=user_id,
        tariff_code=tariff_code,
        active_until=datetime.utcnow() + timedelta(days=duration_days),
    )
    SUBSCRIPTIONS[user_id] = sub
    return sub


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Это самый удобный VPN с оплатой Stars\n\n"
        "3 дня бесплатно — без карты, без регистрации номером",
        reply_markup=get_main_menu(),
    )


@router.message(Command("plans"))
async def cmd_plans(message: Message):
    await message.answer(
        "Доступные тарифы:\n"
        "• Trial — 0⭐️ на 3 дня, до 2 устройств.\n"
        "• Light — 110⭐️ на 30 дней, до 2 устройств, скорость до 100 Mbps.\n"
        "• Family — 200⭐️ на 30 дней, до 5 устройств, скорость до 300 Mbps.\n"
        "• Unlimited — 290⭐️ на 30 дней, до 8 устройств, безлимитная скорость.\n"
        "• Годовая — скидка 35% к месячной цене.",
        reply_markup=get_main_menu(),
    )


@router.message(Command("trial"))
@router.message(F.text == "Попробовать бесплатно")
async def cmd_trial(message: Message):
    sub = _create_subscription(message.from_user.id, "trial")
    await message.answer(
        "Пробный доступ активирован на 3 дня.\n"
        "Конфиг и QR доступны в личном кабинете.",
        reply_markup=get_profile_menu(True),
    )
    logger.info("Trial issued for user %s until %s", sub.user_id, sub.active_until)


@router.message(F.text == "Купить подписку")
async def buy_subscription(message: Message):
    await message.answer(
        "Выберите подходящий тариф — оплата в Stars, выдача конфигурации мгновенно.",
        reply_markup=get_buy_menu(),
    )


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Главное меню",
        reply_markup=get_main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("plan_"))
async def select_plan(callback: CallbackQuery):
    plan_code = callback.data.removeprefix("plan_")
    if plan_code not in TARIFFS:
        await callback.answer("Неизвестный тариф", show_alert=True)
        return

    sub = _create_subscription(callback.from_user.id, plan_code)
    tariff = TARIFFS[plan_code]
    await callback.message.answer(
        f"Тариф {tariff['name']} активирован до {sub.active_until.strftime('%d.%m.%Y')}\n"
        "Конфиг можно скачать или получить как QR в личном кабинете.",
        reply_markup=get_profile_menu(True),
    )
    await callback.answer("Оплата принята, конфиг готов")


@router.message(F.text == "Личный кабинет")
async def profile(message: Message):
    sub = _get_active_subscription(message.from_user.id)
    if not sub:
        await message.answer(
            "У вас нет активной подписки. Выберите действие:",
            reply_markup=get_main_menu(),
        )
        return

    await message.answer(
        f"Подписка {sub.tariff_code} активна до {sub.active_until.strftime('%d.%m.%Y')}",
        reply_markup=get_profile_menu(True),
    )


async def _request_provision(sub: Subscription):
    settings = get_settings()
    payload = {
        "user_id": sub.user_id,
        "protocol": sub.proto,
        "device_name": f"tg-{sub.user_id}",
        "tariff_code": sub.tariff_code,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(f"{settings.provisioner_url}/provision", json=payload)
        response.raise_for_status()
        data = response.json()

        qr_url = data.get("qr_url")
        qr_bytes = b""
        if qr_url:
            qr_resp = await client.get(qr_url)
            qr_resp.raise_for_status()
            qr_bytes = qr_resp.content

    return data, qr_bytes


@router.message(F.text == "Мой конфиг (скачать)")
async def send_config(message: Message):
    sub = _get_active_subscription(message.from_user.id)
    if not sub:
        await message.answer("У вас нет активной подписки", reply_markup=get_main_menu())
        return

    try:
        data, qr_bytes = await _request_provision(sub)
        config_bytes = data.get("config", "").encode()
        filename = f"vpn-{sub.tariff_code}.conf"
        caption = (
            f"Ваша подписка активна до {sub.active_until.strftime('%d.%m.%Y')}\n"
            f"Протокол: {sub.proto.upper()}\n"
            f"Узел: {sub.node_id}\n\n"
            "Инструкция в один клик внутри файла"
        )

        await message.answer_document(
            document=BufferedInputFile(config_bytes, filename=filename),
            caption=caption,
            reply_markup=get_profile_menu(True),
        )

        if qr_bytes:
            await message.answer_photo(
                photo=BufferedInputFile(qr_bytes, filename=f"qr-{sub.tariff_code}.png"),
                caption="Или просто отсканируйте QR",
            )
    except httpx.HTTPError as err:
        logger.error("Config delivery failed: %s", err)
        await message.answer(
            "Ошибка генерации конфига. Пиши в поддержку @evgenii_vpn_support",
            reply_markup=get_main_menu(),
        )


@router.message(F.text == "QR-код")
async def send_qr(message: Message):
    sub = _get_active_subscription(message.from_user.id)
    if not sub:
        await message.answer("Сначала активируйте тариф", reply_markup=get_main_menu())
        return

    try:
        data, qr_bytes = await _request_provision(sub)
        if qr_bytes:
            await message.answer_photo(
                photo=BufferedInputFile(qr_bytes, filename=f"qr-{sub.tariff_code}.png"),
                caption="QR для быстрой настройки",
            )
        else:
            await message.answer(data.get("qr_url", "QR временно недоступен"))
    except httpx.HTTPError as err:
        logger.error("QR delivery failed: %s", err)
        await message.answer("Не удалось загрузить QR. Попробуйте позже", reply_markup=get_profile_menu(True))


@router.message(F.text == "Помощь / FAQ")
async def help_faq(message: Message):
    await message.answer(
        "FAQ:\n- 3 дня бесплатно — без карты.\n- Оплата Stars, выдача мгновенная.\n"
        "- Помощь: @evgenii_vpn_support",
        reply_markup=get_main_menu(),
    )


@router.message(F.text == "Продлить подписку")
async def extend_subscription(message: Message):
    sub = _get_active_subscription(message.from_user.id)
    if not sub:
        await message.answer("Сначала оформите подписку", reply_markup=get_main_menu())
        return
    SUBSCRIPTIONS[message.from_user.id] = Subscription(
        user_id=sub.user_id,
        tariff_code=sub.tariff_code,
        active_until=sub.active_until + timedelta(days=30),
    )
    await message.answer(
        "Подписка продлена ещё на 30 дней",
        reply_markup=get_profile_menu(True),
    )


@router.message(F.text == "Сменить протокол/узел")
async def switch_proto(message: Message):
    sub = _get_active_subscription(message.from_user.id)
    if not sub:
        await message.answer("Сначала оформите подписку", reply_markup=get_main_menu())
        return

    sub.proto = "wireguard" if sub.proto == "amneziawg" else "amneziawg"
    sub.node_id = "default_fra" if sub.node_id == "default_nl" else "default_nl"
    await message.answer(
        f"Протокол переключен на {sub.proto.upper()} (узел {sub.node_id})",
        reply_markup=get_profile_menu(True),
    )


@router.message(F.text == "Статистика трафика")
async def traffic_stats(message: Message):
    sub = _get_active_subscription(message.from_user.id)
    if not sub:
        await message.answer("Нет активной подписки", reply_markup=get_main_menu())
        return
    await message.answer(
        "Статистика скоро появится. Пока держим вас онлайн!",
        reply_markup=get_profile_menu(True),
    )


@router.message(F.text == "« Главное меню")
async def back_home(message: Message):
    await message.answer("Возвращаю главное меню", reply_markup=get_main_menu())


def register_service_routes(dp: Dispatcher):
    dp.include_router(router)


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    register_service_routes(dp)
    return dp


def main():
    settings = get_settings()
    bot = Bot(token=settings.bot_token)
    dp = create_dispatcher()
    logger.info("Bot started with billing backend %s", settings.billing_url)

    async def run_bot():
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Запустить бота"),
                BotCommand(command="plans", description="Посмотреть тарифы"),
                BotCommand(command="trial", description="Получить пробный доступ"),
            ]
        )
        await dp.start_polling(bot)

    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
