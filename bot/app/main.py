import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from .config import get_settings

logging.basicConfig(level=logging.INFO)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я помогу купить подписку на VPN через Telegram Stars."
        "\nИспользуй /plans чтобы увидеть тарифы или /trial для пробного доступа."
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
    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
