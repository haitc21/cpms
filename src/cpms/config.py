"""Typed application settings for CPMS."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

EnvironmentName = Literal["development", "test", "production"]


class Settings(BaseSettings):
    """Environment-backed CPMS configuration."""

    model_config = SettingsConfigDict(
        env_prefix="CPMS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: EnvironmentName = "development"
    service_name: str = "cpms"
    log_level: str = "INFO"
    database_url: str | None = None
    rabbitmq_url: str | None = None
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @model_validator(mode="after")
    def validate_required_urls(self) -> Settings:
        if self.environment == "development":
            if not self.database_url:
                self.database_url = (
                    "postgresql+psycopg://cpms:cpms_dev_password@127.0.0.1:5432/cpms"
                )
            if not self.rabbitmq_url:
                self.rabbitmq_url = "amqp://cmp:cmp_dev_password@127.0.0.1:5672/cmp"
            return self

        if self.environment == "test":
            if not self.database_url:
                self.database_url = (
                    "postgresql+psycopg://cpms:cpms_dev_password@127.0.0.1:5432/cpms"
                )
            if not self.rabbitmq_url:
                self.rabbitmq_url = "amqp://cmp:cmp_dev_password@127.0.0.1:5672/cmp"
            return self

        missing: list[str] = []
        if not self.database_url:
            missing.append("CPMS_DATABASE_URL")
        if not self.rabbitmq_url:
            missing.append("CPMS_RABBITMQ_URL")
        if missing:
            raise ValueError(f"missing required production settings: {', '.join(missing)}")
        return self

    @property
    def require_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError("database_url is not configured")
        return self.database_url

    @property
    def require_rabbitmq_url(self) -> str:
        if not self.rabbitmq_url:
            raise RuntimeError("rabbitmq_url is not configured")
        return self.rabbitmq_url


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
