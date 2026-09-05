from typing import Any, Dict, Optional

from app.vpn.base import VPNProvider


class MockVPNProvider(VPNProvider):
    name = "mock"

    async def health_check(self) -> bool:
        return True

    async def create_account(self, username: str, password: str) -> Dict[str, Any]:
        return {"id": abs(hash(username)) % 1_000_000_000, "username": username, "status": "Active"}

    async def get_account(self, account_id: int) -> Dict[str, Any]:
        return {"id": account_id, "status": "Active"}

    async def disable_account(self, account_id: int) -> Dict[str, Any]:
        return {"id": account_id, "status": "Disabled"}

    async def enable_account(self, account_id: int) -> Dict[str, Any]:
        return {"id": account_id, "status": "Active"}

    async def delete_account(self, account_id: int) -> None:
        return None

    async def get_vless_config(self, account_id: int, server_id: Optional[int] = None) -> Dict[str, Any]:
        return {"protocol": "vless", "configuration": None, "mock": True}

    async def get_wireguard_config(self, account_id: int, server_id: Optional[int] = None) -> Dict[str, Any]:
        return {"protocol": "wireguard", "configuration": None, "mock": True}

    async def get_openvpn_config(self, username: str, password: str, server_id: Optional[int] = None, port_id: Optional[int] = None) -> Dict[str, Any]:
        return {"protocol": "openvpn", "configuration": None, "mock": True}
