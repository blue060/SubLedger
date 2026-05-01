import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ADMIN_PASSWORD: str = ""
    SECRET_KEY: str = "change-me-in-production"
    ENV: str = "production"
    DATABASE_URL: str = "sqlite:////data/subledger.db"
    JWT_EXPIRE_DAYS: int = 7
    EXCHANGE_RATE_API_KEY: str = ""
    EXCHANGE_RATE_CACHE_HOURS: int = 24
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 465
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    SMTP_TLS: bool = True
    BARK_URL: str | None = None
    SERVERCHAN_KEY: str | None = None
    DEFAULT_CURRENCY: str = "CNY"
    REMINDER_DAYS: int = 7
    APP_PORT: int = 8080

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()