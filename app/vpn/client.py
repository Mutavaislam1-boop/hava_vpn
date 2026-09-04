from __future__ import annotations

import httpx

from app.core.config import get_settings


class VpnApiError(RuntimeError):
    pass


class VpnApiClient:
    """Thin client for the external VPN service. No VPN protocol logic lives here."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.vpn_api_url or not settings.vpn_api_key:
            raise VpnApiError("VPN_API_URL and VPN_API_KEY are not configured")
        self.base_url = settings.vpn_api_url.rstrip("/")
        value = settings.vpn_api_key
        if settings.vpn_api_auth_header.lower() == "authorization" and not value.lower().startswith("bearer "):
            value = f"Bearer {value}"
        self.headers = {settings.vpn_api_auth_header: value, "Accept": "application/json"}

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.request(method, f"{self.base_url}{path}", headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except (httpx.HTTPError, ValueError) as exc:
            raise VpnApiError(f"VPN API request failed: {exc}") from exc

    async def create_user(self, username: str, expire_ts: int, traffic_bytes: int | None) -> None:
        await self._request("POST", "/users", json={"username": username, "expires_at": expire_ts, "traffic_limit_bytes": traffic_bytes})

    async def update_user(self, username: str, expire_ts: int, traffic_bytes: int | None) -> None:
        await self._request("PATCH", f"/users/{username}", json={"expires_at": expire_ts, "traffic_limit_bytes": traffic_bytes})

    async def enable_user(self, username: str) -> None:
        await self._request("POST", f"/users/{username}/enable")

    async def disable_user(self, username: str) -> None:
        await self._request("POST", f"/users/{username}/disable")

    async def delete_user(self, username: str) -> None:
        await self._request("DELETE", f"/users/{username}")

    async def get_subscription(self, username: str) -> str:
        data = await self._request("GET", f"/users/{username}/subscription")
        subscription = data.get("subscription") or data.get("config")
        if not subscription:
            raise VpnApiError("VPN API response has no subscription/config field")
        return subscription


def get_vpn_client() -> VpnApiClient:
    return VpnApiClient()
