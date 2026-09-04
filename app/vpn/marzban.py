import httpx
from app.vpn.base import VpnProfile, VpnProvider


class MarzbanProvider(VpnProvider):
    def __init__(self, url: str, username: str, password: str):
        self.url, self.username, self.password = url.rstrip("/"), username, password

    async def _token(self):
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(f"{self.url}/api/admin/token", data={"username": self.username, "password": self.password})
            r.raise_for_status()
            return r.json()["access_token"]

    async def _request(self, method, path, **kwargs):
        token = await self._token()
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.request(method, f"{self.url}{path}", headers={"Authorization": f"Bearer {token}"}, **kwargs)
            r.raise_for_status()
            return r.json() if r.content else {}

    async def create_user(self, username, expire_ts, traffic_bytes):
        data = await self._request("POST", "/api/user", json={"username": username, "expire": expire_ts, "data_limit": traffic_bytes or 0, "data_limit_reset_strategy": "no_reset", "proxies": {"vless": {}}})
        return VpnProfile(username, data.get("subscription_url"))
    async def update_user(self, username, expire_ts, traffic_bytes):
        await self._request("PUT", f"/api/user/{username}", json={"expire": expire_ts, "data_limit": traffic_bytes or 0})
    async def enable_user(self, username): await self._request("POST", f"/api/user/{username}/active")
    async def disable_user(self, username): await self._request("POST", f"/api/user/{username}/disable")
    async def delete_user(self, username): await self._request("DELETE", f"/api/user/{username}")
    async def get_subscription(self, username):
        data = await self._request("GET", f"/api/user/{username}")
        return data["subscription_url"]

