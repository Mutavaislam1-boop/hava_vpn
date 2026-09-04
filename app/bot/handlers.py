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

user_languages: dict[int, str] = {}


def design(title: str, body: str) -> str:
    return f"""
<a href="https://t.me/hava_vpn_bot"> HAVA VPN</a>
<pre>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌬 HAVA VPN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷 {title}

{body}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
</pre>


""".strip()


def get_language(user_id: int) -> str:
    return user_languages.get(user_id, "ru")


def reply_menu() -> ReplyKeyboardMarkup:
    rows = []

    mini_app_url = get_settings().mini_app_url.strip()

    if mini_app_url.startswith("https://"):
        rows.append(
            [
                KeyboardButton(
                    text="🌬 Открыть HAVA VPN",
                    web_app=WebAppInfo(url=mini_app_url),
                )
            ]
        )

    rows.extend(
        [
            [
                KeyboardButton(text="👤 Мой кабинет"),
                KeyboardButton(text="🛍 Магазин"),
            ],
            [
                KeyboardButton(text="❓ Помощь"),
                KeyboardButton(text="ℹ️ О боте"),
            ],
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        is_persistent=True,
    )


def home_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    if language == "en":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🌬 HAVA VPN",
                        callback_data="hava:plans",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🌐 Language",
                        callback_data="hava:language",
                    )
                ],
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌬 HAVA VPN",
                    callback_data="hava:plans",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🌐 Язык",
                    callback_data="hava:language",
                )
            ],
        ]
    )


def plans_keyboard(
    language: str = "ru",
    with_back: bool = True,
) -> InlineKeyboardMarkup:

    if language == "en":
        rows = [
            [
                InlineKeyboardButton(
                    text="📅 1 month",
                    callback_data="hava:month",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⭐ 1 year",
                    callback_data="hava:year",
                )
            ],
        ]

        if with_back:
            rows.append(
                [
                    InlineKeyboardButton(
                        text="⬅️ Back",
                        callback_data="hava:home",
                    )
                ]
            )

    else:
        rows = [
            [
                InlineKeyboardButton(
                    text="📅 1 месяц",
                    callback_data="hava:month",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⭐ 1 год",
                    callback_data="hava:year",
                )
            ],
        ]

        if with_back:
            rows.append(
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data="hava:home",
                    )
                ]
            )

    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )


def plan_keyboard(
    language: str = "ru",
) -> InlineKeyboardMarkup:

    if language == "en":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💳 Buy",
                        callback_data="hava:buy",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Back",
                        callback_data="hava:plans",
                    )
                ],
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Купить",
                    callback_data="hava:buy",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="hava:plans",
                )
            ],
        ]
    )


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇷🇺 Русский",
                    callback_data="lang:ru",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🇬🇧 English",
                    callback_data="lang:en",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="hava:home",
                )
            ],
        ]
    )


def welcome_text(language: str) -> str:
    if language == "en":
        return design(
            "Welcome",
            (
                "Freedom in every connection.\n\n"
                "HAVA VPN is a simple Telegram service "
                "for purchasing and managing VPN access.\n\n"
                "Available features:\n"
                "• VPN subscription purchase\n"
                "• subscription management\n"
                "• personal VPN access\n"
                "• connection through Happ\n"
                "• account management\n"
                "• user support\n\n"
                "Choose a section below."
            ),
        )

    return design(
        "Добро пожаловать",
        (
            "Свобода в каждом соединении.\n\n"
            "HAVA VPN — сервис для быстрого "
            "и удобного подключения к VPN через Telegram.\n\n"
            "Что доступно:\n"
            "• покупка VPN-подписки\n"
            "• управление сроком подписки\n"
            "• персональный VPN-доступ\n"
            "• подключение через Happ\n"
            "• управление аккаунтом\n"
            "• помощь и поддержка\n\n"
            "Выберите нужный раздел ниже."
        ),
    )


def plans_text(language: str) -> str:
    if language == "en":
        return design(
            "Subscription",
            (
                "Choose your HAVA VPN subscription.\n\n"
                "📅 1 month\n"
                "⭐ 1 year"
            ),
        )

    return design(
        "Подписка",
        (
            "Выберите срок подписки HAVA VPN.\n\n"
            "📅 1 месяц\n"
            "⭐ 1 год"
        ),
    )


def month_text(language: str) -> str:
    if language == "en":
        return design(
            "1 month subscription",
            (
                "Period: 30 days\n"
                "Status: available\n\n"
                "Payment will be connected "
                "at the next stage."
            ),
        )

    return design(
        "Подписка на 1 месяц",
        (
            "Срок: 30 дней\n"
            "Статус: доступно\n\n"
            "Оплата будет подключена "
            "на следующем этапе."
        ),
    )


def year_text(language: str) -> str:
    if language == "en":
        return design(
            "1 year subscription",
            (
                "Period: 365 days\n"
                "Status: available\n\n"
                "Payment will be connected "
                "at the next stage."
            ),
        )

    return design(
        "Годовая подписка",
        (
            "Срок: 365 дней\n"
            "Статус: доступно\n\n"
            "Оплата будет подключена "
            "на следующем этапе."
        ),
    )


@router.message(CommandStart())
async def start(message: Message):
    language = get_language(message.from_user.id)

    await message.answer(
        welcome_text(language),
        reply_markup=home_keyboard(language),
    )

    await message.answer(
        "🌬 HAVA VPN",
        reply_markup=reply_menu(),
    )


@router.callback_query(F.data == "hava:home")
async def open_home(callback: CallbackQuery):
    language = get_language(callback.from_user.id)

    await callback.message.edit_text(
        welcome_text(language),
        reply_markup=home_keyboard(language),
    )

    await callback.answer()


@router.callback_query(F.data == "hava:plans")
async def open_plans(callback: CallbackQuery):
    language = get_language(callback.from_user.id)

    await callback.message.edit_text(
        plans_text(language),
        reply_markup=plans_keyboard(language),
    )

    await callback.answer()


@router.callback_query(F.data == "hava:month")
async def open_month(callback: CallbackQuery):
    language = get_language(callback.from_user.id)

    await callback.message.edit_text(
        month_text(language),
        reply_markup=plan_keyboard(language),
    )

    await callback.answer()


@router.callback_query(F.data == "hava:year")
async def open_year(callback: CallbackQuery):
    language = get_language(callback.from_user.id)

    await callback.message.edit_text(
        year_text(language),
        reply_markup=plan_keyboard(language),
    )

    await callback.answer()


@router.callback_query(F.data == "hava:buy")
async def buy_placeholder(callback: CallbackQuery):
    language = get_language(callback.from_user.id)

    if language == "en":
        text = (
            "HAVA VPN payment will be "
            "connected at the next stage."
        )
    else:
        text = (
            "Оплата HAVA VPN будет "
            "подключена следующим этапом."
        )

    await callback.answer(
        text,
        show_alert=True,
    )


@router.callback_query(F.data == "hava:language")
async def open_language(callback: CallbackQuery):
    language = get_language(callback.from_user.id)

    if language == "en":
        text = design(
            "Language",
            "Choose your interface language.",
        )
    else:
        text = design(
            "Язык",
            "Выберите язык интерфейса.",
        )

    await callback.message.edit_text(
        text,
        reply_markup=language_keyboard(),
    )

    await callback.answer()


@router.callback_query(F.data.startswith("lang:"))
async def select_language(callback: CallbackQuery):
    language = callback.data.split(":", 1)[1]

    if language not in {"ru", "en"}:
        await callback.answer()
        return

    user_languages[callback.from_user.id] = language

    await callback.message.edit_text(
        welcome_text(language),
        reply_markup=home_keyboard(language),
    )

    if language == "en":
        await callback.answer(
            "Language changed to English."
        )
    else:
        await callback.answer(
            "Язык изменён на русский."
        )


@router.message(F.text == "👤 Мой кабинет")
async def cabinet(message: Message):
    language = get_language(message.from_user.id)

    if language == "en":
        text = design(
            "My account",
            (
                f"Telegram ID: {message.from_user.id}\n"
                "Subscription: inactive\n"
                "Expiration date: —\n"
                "VPN: disconnected\n"
                "Status: test mode"
            ),
        )
    else:
        text = design(
            "Мой кабинет",
            (
                f"Telegram ID: {message.from_user.id}\n"
                "Подписка: не активна\n"
                "Срок действия: —\n"
                "VPN: не подключён\n"
                "Статус: тестовый режим"
            ),
        )

    await message.answer(text)


@router.message(F.text == "🛍 Магазин")
async def shop(message: Message):
    language = get_language(message.from_user.id)

    if language == "en":
        text = design(
            "HAVA Store",
            "Choose your VPN subscription.",
        )
    else:
        text = design(
            "Магазин HAVA",
            "Выберите VPN-подписку.",
        )

    await message.answer(
        text,
        reply_markup=plans_keyboard(
            language,
            with_back=False,
        ),
    )


@router.message(F.text == "❓ Помощь")
async def help_section(message: Message):
    language = get_language(message.from_user.id)

    if language == "en":
        text = design(
            "Support",
            (
                "If you have problems with "
                "connection, payment or subscription, "
                "contact HAVA support.\n\n"
                "Support will be connected "
                "at the next stage."
            ),
        )
    else:
        text = design(
            "Помощь",
            (
                "Если у вас возникли проблемы "
                "с подключением, оплатой или подпиской, "
                "обратитесь в поддержку HAVA.\n\n"
                "Поддержка будет подключена "
                "на следующем этапе."
            ),
        )

    await message.answer(text)


@router.message(F.text == "ℹ️ О боте")
async def about(message: Message):
    language = get_language(message.from_user.id)

    if language == "en":
        text = design(
            "About HAVA VPN",
            (
                "HAVA VPN is a Telegram service "
                "for purchasing and managing VPN access.\n\n"
                "After purchase, the user receives "
                "personal VPN access and connects "
                "through Happ.\n\n"
                "HAVA means “air” — the brand represents "
                "freedom, simplicity and open internet access."
            ),
        )
    else:
        text = design(
            "О HAVA VPN",
            (
                "HAVA VPN — Telegram-сервис "
                "для покупки и управления VPN-подпиской.\n\n"
                "После покупки пользователь получает "
                "персональный VPN-доступ "
                "и подключается через Happ.\n\n"
                "HAVA означает «воздух» — "
                "бренд связан со свободой, лёгкостью "
                "и свободным доступом к интернету."
            ),
        )

    await message.answer(text)