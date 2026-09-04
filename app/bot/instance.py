import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from app.core.config import get_settings

bot = Bot(get_settings().bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
dp = Dispatcher()
