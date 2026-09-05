from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, LinkPreviewOptions, Message, ReplyKeyboardMarkup, WebAppInfo

from app.core.config import get_settings

router = Router()

BOT_URL = "https://t.me/hava_vpn_bot"
PRIVACY_POLICY_URL = "https://havavpn.com/privacy"
TERMS_URL = "https://havavpn.com/terms"
BANNER_PATH = Path(__file__).parent / "assets" / "hava-banner.mp4"

MONTH_PRICES = {"RUB": "360 ₽", "USD": "$4", "KZT": "2 100 ₸"}
YEAR_PRICES = {"RUB": "4 999 ₽", "USD": "$55", "KZT": "29 000 ₸"}
CURRENCY_CYCLE = {"RUB": "USD", "USD": "KZT", "KZT": "RUB"}
CURRENCY_BUTTONS = {"RUB": "$ USD", "USD": "₸ KZT", "KZT": "₽ RUB"}

user_languages: dict[int, str] = {}
user_currencies: dict[int, str] = {}


async def send_banner(message: Message) -> None:
    await message.answer_video(
        video=FSInputFile(BANNER_PATH),
        supports_streaming=True,
    )


def get_language(user_id: int) -> str:
    return user_languages.get(user_id, "ru")


def mini_app_url(**params: str) -> str:
    parts = urlsplit(get_settings().mini_app_url.strip())
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update(params)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def link_preview() -> LinkPreviewOptions:
    return LinkPreviewOptions(is_disabled=False, url=BOT_URL, prefer_large_media=False, show_above_text=True)


def main_text(language: str, subscription: bool = False) -> str:
    if language == "en":
        title = "Subscription" if subscription else "Welcome"
        return (
            f'<a href="{BOT_URL}"><b>🌬 HAVA VPN</b></a>\n<b>{title}</b>\n\n'
            "Freedom in every connection.\n\n"
            "HAVA VPN is a service for fast and convenient VPN access directly through Telegram.\n\n"
            "Available features:\n• VPN subscription purchase;\n• subscription period management;\n"
            "• personal VPN access;\n• connection through Happ;\n• account management;\n• help and support.\n\n"
            + ("Choose a subscription period below." if subscription else "Choose a section below.")
        )

    title = "Подписка" if subscription else "Добро пожаловать"
    return (
        f'<a href="{BOT_URL}"><b>🌬 HAVA VPN</b></a>\n<b>{title}</b>\n\n'
        "Свобода в каждом соединении.\n\n"
        "HAVA VPN — сервис для быстрого и удобного подключения к VPN прямо через Telegram.\n\n"
        "Что будет доступно:\n• покупка VPN-подписки;\n• управление сроком подписки;\n"
        "• получение персонального VPN-доступа;\n• подключение через Happ;\n• управление аккаунтом;\n• помощь и поддержка.\n\n"
        + ("Выберите срок подписки ниже." if subscription else "Выберите нужный раздел ниже.")
    )


def reply_menu() -> ReplyKeyboardMarkup:
    shop_button = KeyboardButton(text="🛍 Магазин")
    if get_settings().mini_app_url.strip().startswith("https://"):
        shop_button = KeyboardButton(text="🛍 Магазин", web_app=WebAppInfo(url=mini_app_url(section="shop")))
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Мой кабинет"), shop_button],
            [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="ℹ️ О боте")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def home_keyboard(language: str) -> InlineKeyboardMarkup:
    language_label = "🌐 Language" if language == "en" else "🌐 Язык"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌬 HAVA VPN", callback_data="hava:plans")],
        [InlineKeyboardButton(text=language_label, callback_data="hava:language")],
    ])


def language_keyboard(language: str) -> InlineKeyboardMarkup:
    back = "⬅️ Back" if language == "en" else "⬅️ Назад"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"), InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(text=back, callback_data="hava:home")],
    ])


def plans_keyboard(user_id: int, language: str) -> InlineKeyboardMarkup:
    currency = user_currencies.setdefault(user_id, "RUB")
    month = "1 month" if language == "en" else "1 месяц"
    year = "1 year" if language == "en" else "1 год"
    back = "⬅️ Back" if language == "en" else "⬅️ Назад"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📅 {month} — {MONTH_PRICES[currency]}", web_app=WebAppInfo(url=mini_app_url(plan="month")))],
        [InlineKeyboardButton(text=f"⭐ {year} — {YEAR_PRICES[currency]}", web_app=WebAppInfo(url=mini_app_url(plan="year")))],
        [InlineKeyboardButton(text=back, callback_data="hava:home"), InlineKeyboardButton(text=CURRENCY_BUTTONS[currency], callback_data="hava:currency")],
    ])


def about_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔒 Политика конфиденциальности", url=PRIVACY_POLICY_URL)],
        [InlineKeyboardButton(text="📄 Условия использования", url=TERMS_URL)],
    ])


@router.message(CommandStart())
async def start(message: Message):
    language = get_language(message.from_user.id)
    await send_banner(message)
    main_message = await message.answer(main_text(language), reply_markup=reply_menu(), link_preview_options=link_preview())
    try:
        await main_message.edit_reply_markup(reply_markup=home_keyboard(language))
    except TelegramBadRequest:
        # Some Telegram clients may reject replacing a reply keyboard immediately.
        await message.answer(main_text(language), reply_markup=home_keyboard(language), link_preview_options=link_preview())


@router.callback_query(F.data == "hava:home")
async def open_home(callback: CallbackQuery):
    language = get_language(callback.from_user.id)
    await callback.message.edit_text(main_text(language), reply_markup=home_keyboard(language), link_preview_options=link_preview())
    await callback.answer()


@router.callback_query(F.data == "hava:language")
async def open_language(callback: CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=language_keyboard(get_language(callback.from_user.id)))
    await callback.answer()


@router.callback_query(F.data.startswith("lang:"))
async def select_language(callback: CallbackQuery):
    language = callback.data.split(":", 1)[1]
    if language not in {"ru", "en"}:
        await callback.answer()
        return
    user_languages[callback.from_user.id] = language
    await callback.message.edit_text(main_text(language), reply_markup=home_keyboard(language), link_preview_options=link_preview())
    await callback.answer()


@router.callback_query(F.data == "hava:plans")
async def open_plans(callback: CallbackQuery):
    language = get_language(callback.from_user.id)
    user_currencies.setdefault(callback.from_user.id, "RUB")
    await callback.message.edit_text(main_text(language, subscription=True), reply_markup=plans_keyboard(callback.from_user.id, language), link_preview_options=link_preview())
    await callback.answer()


@router.callback_query(F.data == "hava:currency")
async def switch_currency(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_currencies[user_id] = CURRENCY_CYCLE[user_currencies.get(user_id, "RUB")]
    await callback.message.edit_reply_markup(reply_markup=plans_keyboard(user_id, get_language(user_id)))
    await callback.answer()


@router.message(F.text == "👤 Мой кабинет")
async def cabinet(message: Message):
    if get_language(message.from_user.id) == "en":
        text = f"<b>👤 My account</b>\n\nTelegram ID: <code>{message.from_user.id}</code>\nSubscription: inactive\nExpiration date: —\nStatus: test mode"
    else:
        text = f"<b>👤 Мой кабинет</b>\n\nTelegram ID: <code>{message.from_user.id}</code>\nПодписка: не активна\nСрок действия: —\nСтатус: тестовый режим"
    await send_banner(message)
    await message.answer(text)


@router.message(F.text == "🛍 Магазин")
async def shop_fallback(message: Message):
    await send_banner(message)
    await message.answer("Mini App временно недоступен. Проверьте MINI_APP_URL.")


@router.message(F.text == "❓ Помощь")
async def help_section(message: Message):
    if get_language(message.from_user.id) == "en":
        text = "<b>❓ HAVA VPN Help</b>\n\nIf you have problems with connection, payment or subscription, contact support.\n\nSupport will be connected at the next stage."
    else:
        text = "<b>❓ Помощь HAVA VPN</b>\n\nЕсли у вас возникли проблемы с подключением, оплатой или подпиской, обратитесь в поддержку.\n\nПоддержка будет подключена следующим этапом."
    await send_banner(message)
    await message.answer(text)


@router.message(F.text == "ℹ️ О боте")
async def about(message: Message):
    if get_language(message.from_user.id) == "en":
        text = "<b>ℹ️ HAVA VPN</b>\n\nHAVA VPN is a Telegram service for purchasing and managing VPN subscriptions.\n\nAfter purchase, the user receives personal access and connects through Happ.\n\nHAVA means ‘air’ — freedom, lightness and open internet access."
    else:
        text = "<b>ℹ️ HAVA VPN</b>\n\nHAVA VPN — Telegram-сервис для покупки и управления VPN-подпиской.\n\nПосле покупки пользователь получает персональную ссылку или ключ и подключает VPN через Happ.\n\nHAVA означает «воздух» — идея бренда связана со свободой, лёгкостью и свободным доступом к интернету."
    await send_banner(message)
    await message.answer(text, reply_markup=about_keyboard())
