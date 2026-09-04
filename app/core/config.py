from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    expected_bot_username: str = "hava_vpn_bot"
    database_url: str = "sqlite+aiosqlite:///./hava.db"
    public_url: str = "http://localhost:8000"
    mini_app_url: str = ""
    webhook_secret: str = "change-me"
    admin_token: str = "change-me"
    vpn_api_url: str = ""
    vpn_api_key: str = ""
    vpn_api_auth_header: str = "Authorization"
    cors_origins: str = "http://localhost:8000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

    @property
    def resolved_mini_app_url(self) -> str:
        return (self.mini_app_url or self.public_url).strip()

    @property
    def mini_app_ready(self) -> bool:
        return self.resolved_mini_app_url.lower().startswith("https://")

    @property
    def vpn_diagnostic_status(self) -> str:
        url = self.vpn_api_url.strip().lower()
        key = self.vpn_api_key.strip().lower()
        configured = bool(url and key and "provider.example" not in url and key not in {"replace_me", "changeme", "test"})
        return "ONLINE" if configured else "MOCK"


@lru_cache
def get_settings() -> Settings:
    return Settings()
