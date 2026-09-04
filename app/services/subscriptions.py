from __future__ import annotations
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.telegram import token_hash
from app.db.base import Plan, Subscription, SubscriptionStatus, SubscriptionToken, User
from app.vpn import get_vpn_provider


def aware(value):
    if value and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def current_subscription(db: AsyncSession, user_id: int):
    sub = await db.scalar(select(Subscription).where(Subscription.user_id == user_id))
    if sub and sub.status == SubscriptionStatus.ACTIVE and aware(sub.expires_at) <= datetime.now(timezone.utc):
        sub.status = SubscriptionStatus.EXPIRED
        await db.commit()
    return sub


async def provision(db: AsyncSession, user: User, plan: Plan):
    sub = await db.scalar(select(Subscription).where(Subscription.user_id == user.id))
    now = datetime.now(timezone.utc)
    base = max(aware(sub.expires_at), now) if sub and sub.expires_at else now
    expires = base + timedelta(days=plan.duration_days)
    traffic = plan.traffic_limit_gb * 1024**3 if plan.traffic_limit_gb else None
    provider = get_vpn_provider()
    try:
        if not sub:
            sub = Subscription(user_id=user.id, plan_id=plan.id, vpn_username=f"hava_{user.telegram_id}", expires_at=expires)
            db.add(sub)
            await db.flush()
            await provider.create_user(sub.vpn_username, int(expires.timestamp()), traffic)
            raw = secrets.token_urlsafe(32)
            db.add(SubscriptionToken(subscription_id=sub.id, token_hash=token_hash(raw), token=raw))
        else:
            sub.plan_id, sub.expires_at = plan.id, expires
            await provider.update_user(sub.vpn_username, int(expires.timestamp()), traffic)
            await provider.enable_user(sub.vpn_username)
            raw = None
        sub.status, sub.provisioning_error = SubscriptionStatus.ACTIVE, None
        await db.commit()
        return sub, raw
    except Exception as exc:
        if sub:
            sub.status, sub.provisioning_error = SubscriptionStatus.PROVISIONING_ERROR, str(exc)[:1000]
            await db.commit()
        raise


async def rotate_token(db: AsyncSession, sub: Subscription):
    await db.execute(update(SubscriptionToken).where(SubscriptionToken.subscription_id == sub.id).values(is_active=False))
    raw = secrets.token_urlsafe(32)
    db.add(SubscriptionToken(subscription_id=sub.id, token_hash=token_hash(raw), token=raw))
    await db.commit()
    return raw
