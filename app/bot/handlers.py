from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from app.core.config import get_settings

router = Router()

WELCOME_TEXT = """<b>🌬 HAVA VPN</b>
Свобода в каждом соединении.

HAVA VPN — сервис для быстрого и удобного подключения к VPN прямо через Telegram.

Что будет доступно:
• покупка VPN-подписки;
• управление сроком подписки;
• получение персонального VPN-доступа;
• подключение через Happ;
• управление аккаунтом;
• помощь и поддержка.

Выберите нужный раздел ниже."""

PLANS_TEXT = """<b>🌬 HAVA VPN</b>
Управление подпиской

Выберите срок подписки:"""

MONTH_TEXT = """<b>🌬 HAVA VPN</b>
<b>Подписка на 1 месяц</b>

Срок: 30 дней
Статус: доступно

Оплату подключим следующим этапом."""

YEAR_TEXT = """<b>🌬 HAVA VPN</b>
<b>Годовая подписка</b>

Срок: 365 дней
Статус: доступно

Оплату подключим следующим этапом."""

LANGUAGE_TEXT = "<b>🌐 Выберите язык</b>"

user_languages: dict[int, str] = {}


def reply_menu() -> ReplyKeyboardMarkup:
    rows = []
    mini_app_url = get_settings().mini_app_url.strip()
    if mini_app_url.startswith("https://"):
        rows.append([KeyboardButton(text="🌬 Открыть HAVA VPN", web_app=WebAppInfo(url=mini_app_url))])
    rows.extend(
        [
            [KeyboardButton(text="👤 Мой кабинет"), KeyboardButton(text="🛍 Магазин")],
            [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="ℹ️ О боте")],
        ]
    )
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        is_persistent=True,
    )


def home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌬 HAVA VPN", callback_data="hava:plans")],
            [InlineKeyboardButton(text="🌐 Язык", callback_data="hava:language")],
        ]
    )


def plans_keyboard(with_back: bool = True) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📅 1 месяц", callback_data="hava:month")],
        [InlineKeyboardButton(text="⭐ 1 год", callback_data="hava:year")],
    ]
    if with_back:
        rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="hava:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def plan_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Купить", callback_data="hava:buy")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="hava:plans")],
        ]
    )


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:Русский")],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:English")],
            [InlineKeyboardButton(text="🇸🇦 العربية", callback_data="lang:العربية")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="hava:home")],
        ]
    )


@router.message(CommandStart())
async def start(message: Message):
    await message.answer(WELCOME_TEXT, reply_markup=home_keyboard())
    await message.answer("Главное меню HAVA VPN", reply_markup=reply_menu())


@router.callback_query(F.data == "hava:home")
async def open_home(callback: CallbackQuery):
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=home_keyboard())
    await callback.answer()


@router.callback_query(F.data == "hava:plans")
async def open_plans(callback: CallbackQuery):
    await callback.message.edit_text(PLANS_TEXT, reply_markup=plans_keyboard())
    await callback.answer()


@router.callback_query(F.data == "hava:month")
async def open_month(callback: CallbackQuery):
    await callback.message.edit_text(MONTH_TEXT, reply_markup=plan_keyboard())
    await callback.answer()


@router.callback_query(F.data == "hava:year")
async def open_year(callback: CallbackQuery):
    await callback.message.edit_text(YEAR_TEXT, reply_markup=plan_keyboard())
    await callback.answer()


@router.callback_query(F.data == "hava:buy")
async def buy_placeholder(callback: CallbackQuery):
    await callback.answer("Оплата HAVA VPN будет подключена следующим этапом.", show_alert=True)


@router.callback_query(F.data == "hava:language")
async def open_language(callback: CallbackQuery):
    await callback.message.edit_text(LANGUAGE_TEXT, reply_markup=language_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("lang:"))
async def select_language(callback: CallbackQuery):
    language = callback.data.split(":", 1)[1]
    user_languages[callback.from_user.id] = language
    await callback.message.edit_text(
        f"<b>✅ Язык выбран: {language}</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="hava:home")]]
        ),
    )
    await callback.answer()


@router.message(F.text == "👤 Мой кабинет")
async def cabinet(message: Message):
    await message.answer(
        "<b>👤 Мой кабинет</b>\n\n"
        f"Telegram ID: <code>{message.from_user.id}</code>\n"
        "Подписка: не активна\n"
        "Срок действия: —\n"
        "VPN: не подключён\n"
        "Статус проекта: тестовый режим"
    )


@router.message(F.text == "🛍 Магазин")
async def shop(message: Message):
    await message.answer("<b>🛍 Магазин HAVA VPN</b>\n\nВыберите подписку:", reply_markup=plans_keyboard(with_back=False))


@router.message(F.text == "❓ Помощь")
async def help_section(message: Message):
    await message.answer(
        "<b>❓ Помощь HAVA VPN</b>\n\n"
        "Если у вас возникли проблемы с подключением, оплатой или подпиской, обратитесь в поддержку.\n\n"
        "Поддержка будет подключена следующим этапом."
    )


@router.message(F.text == "ℹ️ О боте")
async def about(message: Message):
    await message.answer(
        "<b>ℹ️ HAVA VPN</b>\n\n"
        "HAVA VPN — Telegram-сервис для покупки и управления VPN-подпиской.\n\n"
        "После покупки пользователь получает персональную ссылку или ключ и подключает VPN через Happ.\n\n"
        "HAVA означает «воздух» — идея бренда связана со свободой, лёгкостью и свободным доступом к интернету."
    )
