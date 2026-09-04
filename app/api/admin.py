from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import require_admin
from app.db.base import AdminAuditLog, Order, Payment, Plan, Subscription, SubscriptionStatus, User
from app.db.session import get_db

router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])


class PlanIn(BaseModel):
    name: str; slug: str; description: str = ""; price_stars: int; duration_days: int = 30
    traffic_limit_gb: Optional[int] = None; device_limit: int = 1; server_group: str = "default"; is_active: bool = True; sort_order: int = 0


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count()).select_from(User))
    active = await db.scalar(select(func.count()).select_from(Subscription).where(Subscription.status == SubscriptionStatus.ACTIVE))
    stars = await db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == "SUCCEEDED"))
    pending = await db.scalar(select(func.count()).select_from(Order).where(Order.provisioning_status == "PENDING"))
    return {"users": total, "active_vpn": active, "stars_total": stars, "provisioning_pending": pending}


@router.post("/plans", status_code=201)
async def create_plan(body: PlanIn, db: AsyncSession = Depends(get_db)):
    plan = Plan(**body.model_dump()); db.add(plan); await db.flush()
    db.add(AdminAuditLog(action="CREATE_PLAN", target=f"plan:{plan.id}", details=body.model_dump()))
    await db.commit(); await db.refresh(plan); return plan


@router.put("/plans/{plan_id}")
async def update_plan(plan_id: int, body: PlanIn, db: AsyncSession = Depends(get_db)):
    plan = await db.get(Plan, plan_id)
    if not plan: raise HTTPException(404, "Plan not found")
    for k, v in body.model_dump().items(): setattr(plan, k, v)
    db.add(AdminAuditLog(action="UPDATE_PLAN", target=f"plan:{plan.id}", details=body.model_dump()))
    await db.commit(); return plan


@router.get("/users")
async def users(db: AsyncSession = Depends(get_db)):
    return (await db.scalars(select(User).order_by(User.created_at.desc()).limit(500))).all()
