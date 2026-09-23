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
    api_key: str = ""

    database_url: str = "postgresql+psycopg://mcp:mcp@localhost:5432/mcp_auditor"
    redis_url: str = "redis://localhost:6379/0"

    # Fernet key used to encrypt sensitive fields (e.g. MCPServer.connection_config)
    # at rest. Must be a urlsafe-base64-encoded 32-byte key. Generate with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    encryption_key: str = ""

    # Per-connection timeout (seconds) when discovering tools from an MCP server.
    mcp_discovery_timeout_seconds: float = 15.0
    mcp_allowed_local_commands: list[str] = []
    mcp_sandbox_image: str = "mcp-auditor-mcp-sandbox:latest"
    mcp_execution_memory_limit: str = "256m"
    mcp_execution_cpu_limit: float = 1.0
    mcp_execution_pids_limit: int = 64
    mcp_execution_max_output_bytes: int = 1_048_576

    # Abuse protection uses one fixed window for predictable dashboard behavior.
    rate_limit_window_seconds: int = 60
    rate_limit_requests: int = 120
    rate_limit_discoveries: int = 10
    rate_limit_audits: int = 5
    rate_limit_reports: int = 30
    max_active_audits_per_server: int = 1

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()
