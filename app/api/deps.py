from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.telegram import validate_init_data
from app.db.session import get_db
from app.services.users import get_or_create_user


async def telegram_user(authorization: str = Header(""), db: AsyncSession = Depends(get_db)):
    if not authorization.startswith("tma "):
        raise HTTPException(401, "Use Authorization: tma <initData>")
    tg = validate_init_data(authorization[4:], get_settings().bot_token)
    return await get_or_create_user(db, tg)


def require_admin(x_admin_token: str = Header("")):
    if x_admin_token != get_settings().admin_token:
        raise HTTPException(401, "Invalid admin token")

