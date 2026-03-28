from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PRISM Backend"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./prism.db"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    cloudflare_security_enabled: bool = True
    cloudflare_allow_local_dev: bool = True
    cloudflare_require_ray: bool = False
    cloudflare_min_bot_score: int = 20
    cloudflare_rate_limit_window_seconds: int = 60
    cloudflare_rate_limit_max_requests: int = 120
    cloudflare_block_countries: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
