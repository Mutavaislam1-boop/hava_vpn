import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from app.core.config import get_settings
from app.core.database import db
from app.vpn import get_vpn_provider

PLAN_DAYS = {"month": 30, "year": 365}


def _public_url() -> str:
    settings = get_settings()
    return (settings.public_url or settings.mini_app_url).rstrip("/")


def subscription_url(record: Dict[str, Any]) -> str:
    token = record.get("subscription_token")
    return f"{_public_url()}/s/{token}" if token and _public_url() else ""


async def provision_paid_subscription(telegram_id: int, plan: str) -> Dict[str, Any]:
    """Call only after a payment has been independently confirmed.

    Idempotent for an already provisioned Telegram user. Account creation is never retried.
    """
    if plan not in PLAN_DAYS:
        raise ValueError("Unknown subscription plan")
    provider = get_vpn_provider()
    current = await db.get_subscription(telegram_id)
    now = datetime.now(timezone.utc)
    base = now
    if current and current.get("subscription_expires_at"):
        existing_expiry = datetime.fromisoformat(current["subscription_expires_at"])
        if existing_expiry > now:
            base = existing_expiry
    expires = base + timedelta(days=PLAN_DAYS[plan])

    if current and current.get("vpnresellers_account_id"):
        account = await provider.enable_account(int(current["vpnresellers_account_id"]))
        password = current.get("vpnresellers_password")
        token = current.get("subscription_token") or secrets.token_urlsafe(32)
        started = current.get("subscription_started_at") or now.isoformat()
    else:
        suffix = secrets.token_hex(2)
        username = f"hava_{telegram_id}_{suffix}"[:50]
        password = secrets.token_urlsafe(18)[:50]
        account = await provider.create_account(username, password)
        token = secrets.token_urlsafe(32)
        started = now.isoformat()

    record = {
        "telegram_user_id": telegram_id,
        "vpnresellers_account_id": int(account["id"]),
        "vpnresellers_username": account.get("username") or (current or {}).get("vpnresellers_username"),
        "vpnresellers_password": password,
        "vpn_status": "active",
        "plan": plan,
        "subscription_started_at": started,
        "subscription_expires_at": expires.isoformat(),
        "subscription_token": token,
        "subscription_token_hash": hashlib.sha256(token.encode()).hexdigest(),
    }
    await db.save_subscription(record)
    return record


async def disable_expired_subscription(record: Dict[str, Any]) -> Dict[str, Any]:
    account_id = record.get("vpnresellers_account_id")
    if account_id and record.get("vpn_status") != "disabled":
        await get_vpn_provider().disable_account(int(account_id))
        record["vpn_status"] = "disabled"
        await db.save_subscription(record)
    return record
