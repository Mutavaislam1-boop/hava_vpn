import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from app.api import admin, subscription, user
from app.bot import dp
from app.bot.instance import bot
from app.core.config import get_settings
from app.db import Base, SessionLocal, engine
from app.db.base import Node, Plan

s = get_settings()


async def seed():
    async with SessionLocal() as db:
        if not await db.scalar(select(Plan.id).limit(1)):
            db.add_all([
                Plan(name="HAVA Start", slug="start", description="Для одного устройства", price_stars=199, duration_days=30, traffic_limit_gb=100, device_limit=1, sort_order=1),
                Plan(name="HAVA Plus", slug="plus", description="Баланс скорости и свободы", price_stars=399, duration_days=30, traffic_limit_gb=500, device_limit=3, sort_order=2),
                Plan(name="HAVA Pro", slug="pro", description="Максимум возможностей", price_stars=699, duration_days=30, traffic_limit_gb=None, device_limit=5, sort_order=3),
            ])
        if not await db.scalar(select(Node.id).limit(1)):
            db.add(Node(name="HAVA Germany 01", country="DE", city="Frankfurt", hostname="vpn.example.com", provider="mock", status="ONLINE", load="low"))
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed()
    polling = None
    if s.public_url.startswith("http://localhost"):
        await bot.delete_webhook(drop_pending_updates=False)
        polling = asyncio.create_task(dp.start_polling(bot))
    yield
    if polling:
        polling.cancel()
        with suppress(asyncio.CancelledError): await polling
    await bot.session.close()
    await engine.dispose()


app = FastAPI(title="HAVA VPN", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=s.origins, allow_credentials=False, allow_methods=["GET", "POST", "PUT"], allow_headers=["Authorization", "Content-Type", "X-Admin-Token"])
app.include_router(user.router)
app.include_router(subscription.router)
app.include_router(admin.router)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/", include_in_schema=False)
async def mini_app(): return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/admin", include_in_schema=False)
async def admin_app(): return FileResponse(Path(__file__).parent / "static" / "admin.html")


@app.get("/health")
async def health(): return {"status": "ok", "service": "HAVA VPN"}


@app.post("/telegram/webhook/{secret}", include_in_schema=False)
async def telegram_webhook(secret: str, request: Request, x_telegram_bot_api_secret_token: str = Header("")):
    if secret != s.webhook_secret or x_telegram_bot_api_secret_token != s.webhook_secret:
        raise HTTPException(403)
    await dp.feed_update(bot, Update.model_validate(await request.json()))
    return {"ok": True}

