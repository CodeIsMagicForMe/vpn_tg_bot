import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, KeyboardButton, Message, ReplyKeyboardMarkup
from .config import get_settings

logging.basicConfig(level=logging.INFO)
router = Router()

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/plans"), KeyboardButton(text="/trial")],
        [KeyboardButton(text="/start")],
    ],
    resize_keyboard=True,
)


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
