import io
import qrcode
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import telegram_user
from app.core.config import get_settings
from app.db.base import Device, Node, Order, Plan, Subscription, SubscriptionToken, SupportTicket, User
from app.bot.instance import bot
from app.db.session import get_db
from app.services.subscriptions import current_subscription, rotate_token

router = APIRouter(prefix="/api")


@router.get("/plans")
async def plans(db: AsyncSession = Depends(get_db)):
    rows = (await db.scalars(select(Plan).where(Plan.is_active).order_by(Plan.sort_order))).all()
    return [{"id": p.id, "name": p.name, "slug": p.slug, "description": p.description, "price_stars": p.price_stars, "duration_days": p.duration_days, "traffic_limit_gb": p.traffic_limit_gb, "device_limit": p.device_limit} for p in rows]


class OrderIn(BaseModel):
    plan_id: int


@router.post("/orders", status_code=201)
async def create_order(body: OrderIn, user: User = Depends(telegram_user), db: AsyncSession = Depends(get_db)):
    plan = await db.get(Plan, body.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(404, "Plan not found")
    order = Order(user_id=user.id, plan_id=plan.id, amount=plan.price_stars)
    db.add(order); await db.commit(); await db.refresh(order)
    invoice = await bot.create_invoice_link(title=plan.name, description=f"HAVA VPN на {plan.duration_days} дней", payload=f"order:{order.id}", currency="XTR", prices=[{"label": plan.name, "amount": plan.price_stars}])
    return {"order_id": order.id, "invoice_url": invoice}


@router.get("/me")
async def me(user: User = Depends(telegram_user), db: AsyncSession = Depends(get_db)):
    sub = await db.scalar(select(Subscription).options(selectinload(Subscription.plan)).where(Subscription.user_id == user.id))
    devices = len((await db.scalars(select(Device).where(Device.user_id == user.id, Device.is_active))).all())
    token = await db.scalar(select(SubscriptionToken).where(SubscriptionToken.subscription_id == sub.id, SubscriptionToken.is_active)) if sub else None
    return {"hava_id": user.id, "telegram_id": user.telegram_id, "username": user.username, "first_name": user.first_name, "subscription": None if not sub else {"status": sub.status.value, "plan": sub.plan.name, "expires_at": sub.expires_at, "traffic_used_bytes": sub.traffic_used_bytes, "traffic_limit_gb": sub.plan.traffic_limit_gb, "devices": devices, "device_limit": sub.plan.device_limit, "subscription_url": f"{get_settings().public_url}/s/{token.token}" if token else None}}


@router.get("/servers")
async def servers(db: AsyncSession = Depends(get_db)):
    nodes = (await db.scalars(select(Node).where(Node.status.in_(["ONLINE", "DEGRADED"])))).all()
    return [{"name": n.name, "country": n.country, "city": n.city, "status": n.status, "load": n.load} for n in nodes]


@router.get("/me/devices")
async def devices(user: User = Depends(telegram_user), db: AsyncSession = Depends(get_db)):
    return (await db.scalars(select(Device).where(Device.user_id == user.id, Device.is_active))).all()


class TicketIn(BaseModel):
    category: str = Field(max_length=50)
    message: str = Field(min_length=3, max_length=4000)


@router.post("/support", status_code=201)
async def support(body: TicketIn, user: User = Depends(telegram_user), db: AsyncSession = Depends(get_db)):
    ticket = SupportTicket(user_id=user.id, category=body.category, message=body.message)
    db.add(ticket); await db.commit(); await db.refresh(ticket)
    return {"ticket_id": ticket.id, "status": ticket.status}


@router.post("/vpn/rotate")
async def rotate(user: User = Depends(telegram_user), db: AsyncSession = Depends(get_db)):
    sub = await current_subscription(db, user.id)
    if not sub:
        raise HTTPException(404, "Subscription not found")
    raw = await rotate_token(db, sub)
    return {"subscription_url": f"{get_settings().public_url}/s/{raw}"}


@router.get("/vpn/qr")
async def qr(url: str, user: User = Depends(telegram_user)):
    expected = get_settings().public_url.rstrip("/") + "/s/"
    if not url.startswith(expected):
        raise HTTPException(400, "Invalid subscription URL")
    image = qrcode.make(url); stream = io.BytesIO(); image.save(stream, format="PNG")
    return Response(stream.getvalue(), media_type="image/png")
