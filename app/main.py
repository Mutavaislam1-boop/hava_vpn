import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from aiogram import Dispatcher
from fastapi import FastAPI

from app.bot import router
from app.bot.instance import bot
from app.core.config import get_settings
from app.web import app as web_app


def design(title: str, body: str) -> str:
    if str(title).strip().upper() in GENERATION_STYLE_TITLES:
        return model_design(str(title), str(body))

    current_time = datetime.now().strftime("%H:%M • %d.%m.%y")

    return f"""
<a href="https://t.me/hava_vpn_bot"> HAVA {current_time}</a>
<pre>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>🏷{title}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{body}
</pre>
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    polling = None
    try:
        identity = await bot.get_me()
        logging.info("HAVA VPN bot started: @%s (ID %s)", identity.username, identity.id)
        await bot.delete_webhook(drop_pending_updates=False)
        polling = asyncio.create_task(dispatcher.start_polling(bot))
    except Exception as exc:
        logging.error("Telegram polling failed; Mini App remains available: %s", exc)
    yield
    if polling:
        polling.cancel()
        with suppress(asyncio.CancelledError):
            await polling
    await bot.session.close()


web_app.router.lifespan_context = lifespan
app = web_app


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)
