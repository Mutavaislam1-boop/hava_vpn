from app.vpn.base import VpnProfile, VpnProvider


class MockVpnProvider(VpnProvider):
    async def create_user(self, username, expire_ts, traffic_bytes):
        return VpnProfile(username)
    async def update_user(self, username, expire_ts, traffic_bytes): pass
    async def enable_user(self, username): pass
    async def disable_user(self, username): pass
    async def delete_user(self, username): pass
    async def get_subscription(self, username):
        return f"vless://demo-{username}@vpn.example.com:443?security=reality&type=tcp#HAVA-Smart"

