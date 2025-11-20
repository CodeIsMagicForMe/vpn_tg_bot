import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, KeyboardButton, Message, ReplyKeyboardMarkup
from .config import get_settings
# Explicit import from the concrete keyboards module avoids cases where
# partial package imports leave helpers unavailable at runtime (seen as
# NameError in docker logs).
from .keyboards.main_kb import get_buy_menu, get_main_menu, get_profile_menu

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = Router()

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/plans"), KeyboardButton(text="/trial")],
        [KeyboardButton(text="/start")],
    ],
    resize_keyboard=True,
)


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
        "Привет! Я помогу купить подписку на VPN через Telegram Stars."
        "\nИспользуй кнопки ниже, чтобы узнать тарифы или получить пробный доступ.",
        reply_markup=MAIN_KEYBOARD,
    )


@router.message(Command("plans"))
async def cmd_plans(message: Message):
    await message.answer(
        "Доступные тарифы:\n"
        "• Trial — 0⭐️ на 3 дня, до 2 устройств.\n"
        "• Light — 110⭐️ на 30 дней, до 2 устройств, скорость до 100 Mbps.\n"
        "• Family — 200⭐️ на 30 дней, до 5 устройств, скорость до 300 Mbps.\n"
        "• Unlimited — 290⭐️ на 30 дней, до 8 устройств, безлимитная скорость.",
        reply_markup=MAIN_KEYBOARD,
    )


@router.message(Command("trial"))
async def cmd_trial(message: Message):
    await message.answer(
        "Пробный доступ на 3 дня оформляется мгновенно и без оплаты."
        "\nНажмите кнопку /trial ещё раз или отправьте /trial вручную, чтобы получить пробный тариф.",
        reply_markup=MAIN_KEYBOARD,
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
    logging.info("Bot started with billing backend %s", settings.billing_url)

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
