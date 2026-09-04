from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.telegram import token_hash
from app.db.base import Subscription, SubscriptionStatus, SubscriptionToken
from app.db.session import get_db
from app.services.subscriptions import aware
from app.vpn import get_vpn_client
from datetime import datetime, timezone

router = APIRouter()


@router.get("/s/{token}", response_class=PlainTextResponse)
async def subscription(token: str, db: AsyncSession = Depends(get_db)):
    item = await db.scalar(select(SubscriptionToken).where(SubscriptionToken.token_hash == token_hash(token), SubscriptionToken.is_active))
    if not item:
        raise HTTPException(404, "Subscription link is invalid or revoked")
    sub = await db.scalar(select(Subscription).where(Subscription.id == item.subscription_id))
    if sub.status != SubscriptionStatus.ACTIVE or aware(sub.expires_at) <= datetime.now(timezone.utc):
        raise HTTPException(403, "Subscription is not active")
    return await get_vpn_client().get_subscription(sub.vpn_username)
