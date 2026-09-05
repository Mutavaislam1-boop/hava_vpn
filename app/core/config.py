from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    mini_app_url: str = ""
    public_url: str = ""
    host: str = "0.0.0.0"
    port: int = 8000
    database_path: str = "hava.db"
    vpn_provider: str = "mock"
    vpnresellers_base_url: str = "https://api.vpnresellers.com/v4_1"
    vpnresellers_api_token: str = ""
    vpnresellers_timeout: float = 15.0
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
