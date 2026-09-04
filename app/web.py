from pathlib import Path

from fastapi import Depends, FastAPI, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.telegram import validate_init_data

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


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/me")
async def me(user: dict = Depends(telegram_user)):
    return {
        "hava_id": f"H{user['id']}",
        "telegram_id": user["id"],
        "username": user.get("username"),
        "first_name": user.get("first_name", "Пользователь"),
        "subscription": None,
    }


@app.get("/api/plans")
async def plans():
    return PLANS


@app.get("/api/subscription")
async def subscription(user: dict = Depends(telegram_user)):
    return {"status": "INACTIVE", "plan": None, "expires_at": None, "devices": 0, "device_limit": 0}


@app.get("/api/vpn")
async def vpn(user: dict = Depends(telegram_user)):
    return {"status": "NOT_PROVISIONED", "subscription_url": None, "happ_url": None}


@app.post("/api/order")
async def order(user: dict = Depends(telegram_user)):
    return {"status": "MOCK", "message": "Оплата будет подключена на следующем этапе"}


@app.post("/api/vpn/rotate")
async def rotate(user: dict = Depends(telegram_user)):
    return {"status": "MOCK", "message": "VPN пока не активирован"}


@app.get("/api/vpn/qr")
async def qr(user: dict = Depends(telegram_user)):
    return {"status": "MOCK", "qr": None}
