import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🌬 HAVA VPN\n\n"
        "✅ Бот подключён и работает.\n"
        f"Ваш Telegram ID: {message.from_user.id}"
    )

async def main():
    me = await bot.get_me()
    print(f"CONNECTED BOT: @{me.username} / ID: {me.id}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())