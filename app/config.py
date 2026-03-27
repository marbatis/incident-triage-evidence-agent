from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Incident Triage Evidence Agent"
    environment: str = "dev"
    debug: bool = False

    database_url: str = "sqlite:///./triage.db"
    max_upload_bytes: int = 1_000_000

    provider_mode: Literal["auto", "mock", "openai"] = "auto"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-5-mini"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def normalized_database_url(self) -> str:
        # Heroku may still provide postgres:// URLs.
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql://", 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
