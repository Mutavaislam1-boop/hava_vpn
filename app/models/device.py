from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    device_name = Column(String(100), nullable=False)
    device_type = Column(String(30), nullable=False)

    device_uuid = Column(String(255), unique=True, nullable=False, index=True)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship(
        "User",
        back_populates="devices",
    )
    vpn_configs = relationship(
        "VpnConfig",
        cascade="all, delete-orphan",
    )