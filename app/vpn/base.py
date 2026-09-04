from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VpnProfile:
    username: str
    subscription_url: str | None = None


class VpnProvider(ABC):
    @abstractmethod
    async def create_user(self, username: str, expire_ts: int, traffic_bytes: int | None) -> VpnProfile: ...
    @abstractmethod
    async def update_user(self, username: str, expire_ts: int, traffic_bytes: int | None) -> None: ...
    @abstractmethod
    async def enable_user(self, username: str) -> None: ...
    @abstractmethod
    async def disable_user(self, username: str) -> None: ...
    @abstractmethod
    async def delete_user(self, username: str) -> None: ...
    @abstractmethod
    async def get_subscription(self, username: str) -> str: ...
