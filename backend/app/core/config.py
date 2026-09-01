"""Application configuration.

Settings are loaded from process environment variables, falling back to the
project's root ``.env`` file. Centralizing configuration here keeps
environment-specific values out of the rest of the codebase.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> repo root is three levels up.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ROOT_ENV_FILE = _REPO_ROOT / ".env"


class Settings(BaseSettings):
    """Centralized application settings."""

    model_config = SettingsConfigDict(
        env_file=(_ROOT_ENV_FILE, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "MCP Server Auditor"
    app_version: str = "0.1.0"
    app_env: str = "development"
    log_level: str = "INFO"

    api_prefix: str = "/api/v1"

    cors_origins: list[str] = ["http://localhost:3000"]

    database_url: str = "postgresql+psycopg://mcp:mcp@localhost:5432/mcp_auditor"
    redis_url: str = "redis://localhost:6379/0"

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()
