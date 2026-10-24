from __future__ import annotations

from enum import StrEnum

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    db_url: SecretStr = SecretStr("sqlite:///./alfa-credit-hub.db")
    log_level: LogLevel = LogLevel.INFO
    auth_secret: SecretStr = SecretStr("local-development-secret-change-before-deploy")
    auth_cookie_secure: bool = False

    @field_validator("auth_secret")
    @classmethod
    def auth_secret_must_be_long_enough(cls, secret: SecretStr) -> SecretStr:
        if len(secret.get_secret_value()) < 32:
            raise ValueError("AUTH_SECRET must contain at least 32 characters")
        return secret

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
