from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from app.core.config import get_settings

bot = Bot(get_settings().bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
