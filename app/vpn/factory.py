from functools import lru_cache

from app.core.config import get_settings
from app.vpn.base import VPNProvider
from app.vpn.mock import MockVPNProvider
from app.vpn.vpnresellers import VPNResellersProvider


@lru_cache
def get_vpn_provider() -> VPNProvider:
    settings = get_settings()
    if settings.vpn_provider.lower() == "vpnresellers":
        return VPNResellersProvider(settings.vpnresellers_base_url, settings.vpnresellers_api_token, settings.vpnresellers_timeout)
    return MockVPNProvider()
