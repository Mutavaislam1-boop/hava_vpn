import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from app.vpn.base import VPNProvider, VPNProviderError

logger = logging.getLogger(__name__)


class VPNResellersProvider(VPNProvider):
    name = "vpnresellers"

    def __init__(self, base_url: str, token: str, timeout: float = 15.0):
        if not token:
            raise ValueError("VPNRESELLERS_API_TOKEN is not configured")
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}", "Accept": "application/json", "Content-Type": "application/json"}
        self.timeout = timeout

    async def _request(self, method: str, path: str, *, params=None, json=None, safe_retry: bool = False) -> Dict[str, Any]:
        attempts = 2 if safe_retry else 1
        for attempt in range(attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                    response = await client.request(method, f"{self.base_url}{path}", params=params, json=json)
                if response.status_code < 400:
                    return response.json() if response.content else {}
                try:
                    detail = response.json().get("message", "VPN provider request failed")
                except ValueError:
                    detail = "VPN provider request failed"
                if response.status_code == 402:
                    logger.error("VPNResellers has insufficient balance")
                    detail = "VPN provider balance is insufficient"
                raise VPNProviderError(detail, response.status_code)
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt + 1 < attempts:
                    await asyncio.sleep(0.25)
                    continue
                raise VPNProviderError("VPN provider is temporarily unavailable", 503) from exc
        raise VPNProviderError("VPN provider request failed")

    async def health_check(self) -> bool:
        await self._request("GET", "/accounts", params={"per_page": 1}, safe_retry=True)
        return True

    async def create_account(self, username: str, password: str) -> Dict[str, Any]:
        return (await self._request("POST", "/accounts", json={"username": username, "password": password}))["data"]

    async def get_account(self, account_id: int) -> Dict[str, Any]:
        return (await self._request("GET", f"/accounts/{account_id}", safe_retry=True))["data"]

    async def disable_account(self, account_id: int) -> Dict[str, Any]:
        return (await self._request("PUT", f"/accounts/{account_id}/disable"))["data"]

    async def enable_account(self, account_id: int) -> Dict[str, Any]:
        return (await self._request("PUT", f"/accounts/{account_id}/enable"))["data"]

    async def delete_account(self, account_id: int) -> None:
        await self._request("DELETE", f"/accounts/{account_id}")

    async def _first_id(self, path: str) -> int:
        payload = await self._request("GET", path, safe_retry=True)
        items = payload.get("data", [])
        if not items:
            raise VPNProviderError(f"No VPN provider resources at {path}", 503)
        preferred = next((item for item in items if item.get("default")), items[0])
        return int(preferred["id"])

    async def get_vless_config(self, account_id: int, server_id: Optional[int] = None) -> Dict[str, Any]:
        server_id = server_id or await self._first_id("/vless-servers")
        data = await self._request("GET", "/configuration/vless", params={"server_id": server_id, "account_id": account_id}, safe_retry=True)
        return {"protocol": "vless", "server_id": server_id, "configuration": data.get("data", data)}

    async def get_wireguard_config(self, account_id: int, server_id: Optional[int] = None) -> Dict[str, Any]:
        server_id = server_id or await self._first_id("/servers")
        data = await self._request("GET", "/configuration/wireguard", params={"server_id": server_id, "account_id": account_id}, safe_retry=True)
        return {"protocol": "wireguard", "server_id": server_id, "configuration": data.get("data", data)}

    async def get_openvpn_config(self, username: str, password: str, server_id: Optional[int] = None, port_id: Optional[int] = None) -> Dict[str, Any]:
        server_id = server_id or await self._first_id("/servers")
        port_id = port_id or await self._first_id("/ports")
        data = await self._request("GET", "/configuration/openvpn", params={"server_id": server_id, "port_id": port_id}, safe_retry=True)
        return {"protocol": "openvpn", "server_id": server_id, "port_id": port_id, "configuration": data.get("data", data)}
