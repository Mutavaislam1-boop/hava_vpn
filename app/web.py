from pathlib import Path

import hashlib
import io
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException
import qrcode
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.telegram import validate_init_data
from app.core.database import db
from app.services.subscriptions import disable_expired_subscription, subscription_url
from app.vpn import get_vpn_provider
from app.vpn.base import VPNProviderError

STATIC_DIR = Path(__file__).parent / "static"

PLANS = [
    {"id": "month", "name": "HAVA Month", "duration_days": 30, "device_limit": 1, "traffic": "100 GB", "price": 365, "currency": "RUB", "featured": False},
    {"id": "year", "name": "HAVA Year", "duration_days": 365, "device_limit": 3, "traffic": "Безлимит", "price": 4999, "currency": "RUB", "featured": True},
]


def telegram_user(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("tma "):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Open HAVA VPN inside Telegram")
    return validate_init_data(authorization[4:], get_settings().bot_token)


app = FastAPI(title="HAVA VPN Mini App", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/privacy", include_in_schema=False)
async def privacy_policy():
    return FileResponse(STATIC_DIR / "privacy.html")


@app.get("/terms", include_in_schema=False)
async def terms_of_use():
    return FileResponse(STATIC_DIR / "terms.html")


@app.get("/health")
async def health():
    try:
        provider = get_vpn_provider().name
    except ValueError:
        provider = "not_configured"
    return {"status": "ok", "database": "online", "vpn_provider": provider}


@app.get("/api/me")
async def me(user: dict = Depends(telegram_user)):
    await db.upsert_user(user)
    record = await db.get_subscription(user["id"])
    return {
        "hava_id": f"H{user['id']}",
        "telegram_id": user["id"],
        "username": user.get("username"),
        "first_name": user.get("first_name", "Пользователь"),
        "subscription": record,
    }


@app.get("/api/plans")
async def plans():
    return PLANS


@app.get("/api/subscription")
async def subscription(user: dict = Depends(telegram_user)):
    await db.upsert_user(user)
    record = await db.get_subscription(user["id"])
    if not record:
        return {"status": "INACTIVE", "plan": None, "expires_at": None, "devices": 0, "device_limit": 0}
    expires = record.get("subscription_expires_at")
    if expires and datetime.fromisoformat(expires) <= datetime.now(timezone.utc):
        record = await disable_expired_subscription(record)
    return {"status": record["vpn_status"].upper(), "plan": record["plan"], "expires_at": expires, "devices": 1, "device_limit": 1 if record["plan"] == "month" else 3}


@app.get("/api/vpn")
async def vpn(user: dict = Depends(telegram_user)):
    await db.upsert_user(user)
    record = await db.get_subscription(user["id"])
    if not record:
        return {"status": "NOT_PROVISIONED", "subscription_url": None, "happ_url": None, "qr_available": False}
    url = subscription_url(record)
    return {"status": record["vpn_status"].upper(), "plan": record["plan"], "expires_at": record["subscription_expires_at"], "protocol": "vless", "subscription_url": url or None, "happ_url": url or None, "qr_available": bool(url)}


@app.post("/api/order")
async def order(user: dict = Depends(telegram_user)):
    return {"status": "MOCK", "message": "Оплата будет подключена на следующем этапе"}


@app.post("/api/vpn/rotate")
async def rotate(user: dict = Depends(telegram_user)):
    return {"status": "MOCK", "message": "VPN пока не активирован"}


@app.get("/api/vpn/qr")
async def qr(user: dict = Depends(telegram_user)):
    record = await db.get_subscription(user["id"])
    url = subscription_url(record) if record else ""
    if not url:
        raise HTTPException(status_code=404, detail="VPN is not provisioned")
    image = qrcode.make(url)
    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return StreamingResponse(output, media_type="image/png", headers={"Cache-Control": "no-store"})


@app.get("/s/{token}", response_class=PlainTextResponse, include_in_schema=False)
async def hava_subscription(token: str):
    if len(token) < 32:
        raise HTTPException(status_code=404, detail="Subscription not found")
    record = await db.get_subscription_by_token_hash(hashlib.sha256(token.encode()).hexdigest())
    if not record or record.get("subscription_token") != token:
        raise HTTPException(status_code=404, detail="Subscription not found")
    expires = record.get("subscription_expires_at")
    if not expires or datetime.fromisoformat(expires) <= datetime.now(timezone.utc):
        await disable_expired_subscription(record)
        raise HTTPException(status_code=403, detail="Subscription expired")
    if record.get("vpn_status") != "active":
        raise HTTPException(status_code=403, detail="Subscription disabled")
    try:
        config = await get_vpn_provider().get_vless_config(int(record["vpnresellers_account_id"]))
    except VPNProviderError as exc:
        raise HTTPException(status_code=503, detail="VPN configuration is temporarily unavailable") from exc
    payload = config.get("configuration") or {}
    content = payload.get("content") if isinstance(payload, dict) else str(payload)
    if not content:
        raise HTTPException(status_code=503, detail="VPN configuration is not ready")
    return PlainTextResponse(content, media_type="text/plain; charset=utf-8", headers={"Cache-Control": "no-store"})
