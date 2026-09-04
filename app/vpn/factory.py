from app.core.config import get_settings
from app.vpn.marzban import MarzbanProvider
from app.vpn.mock import MockVpnProvider


def get_vpn_provider():
    s = get_settings()
    if s.vpn_provider == "marzban":
        return MarzbanProvider(s.marzban_url, s.marzban_username, s.marzban_password)
    return MockVpnProvider()

