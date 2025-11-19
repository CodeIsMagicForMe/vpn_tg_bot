from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def get_main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    buttons = [
        "Попробовать бесплатно",
        "Купить подписку",
        "Личный кабинет",
        "Помощь / FAQ",
    ]
    for btn in buttons:
        builder.add(KeyboardButton(text=btn))
    builder.adjust(2)
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
        selective=True,
    )


def get_buy_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Light — 110 Stars/мес", callback_data="plan_light"))
    builder.add(InlineKeyboardButton(text="Family — 200 Stars/мес", callback_data="plan_family"))
    builder.add(InlineKeyboardButton(text="Unlimited — 290 Stars/мес", callback_data="plan_unlimited"))
    builder.add(InlineKeyboardButton(text="Годовая подписка (–35%)", callback_data="plan_year"))
    builder.add(InlineKeyboardButton(text="« Назад", callback_data="back_main"))
    builder.adjust(1)
    return builder.as_markup()


def get_profile_menu(has_active_sub: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Мой конфиг (скачать)"))
    builder.add(KeyboardButton(text="QR-код"))
    if has_active_sub:
        builder.add(KeyboardButton(text="Продлить подписку"))
        builder.add(KeyboardButton(text="Сменить протокол/узел"))
    builder.add(KeyboardButton(text="Статистика трафика"))
    builder.add(KeyboardButton(text="« Главное меню"))
    builder.adjust(2)
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Ваш личный кабинет",
        selective=True,
    )


def get_admin_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Админ: метрики"))
    builder.add(KeyboardButton(text="Админ: рассылка"))
    builder.add(KeyboardButton(text="Админ: обратно"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Админ-панель", selective=True)
