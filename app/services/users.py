from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import User


async def get_or_create_user(db: AsyncSession, tg: dict, referrer_id: int | None = None) -> User:
    user = await db.scalar(select(User).where(User.telegram_id == int(tg["id"])))
    if not user:
        user = User(telegram_id=int(tg["id"]), username=tg.get("username"), first_name=tg.get("first_name"), language=tg.get("language_code", "ru"), referrer_id=referrer_id)
        db.add(user)
    else:
        user.username, user.first_name = tg.get("username"), tg.get("first_name")
    await db.commit()
    await db.refresh(user)
    return user
