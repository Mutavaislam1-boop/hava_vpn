from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    bot_username: str = "hava_vpn_bot"
    database_url: str = "sqlite+aiosqlite:///./hava.db"
    public_url: str = "http://localhost:8000"
    webhook_secret: str = "change-me"
    admin_token: str = "change-me"
    vpn_provider: str = "mock"
    marzban_url: str = ""
    marzban_username: str = ""
    marzban_password: str = ""
    cors_origins: str = "http://localhost:8000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
