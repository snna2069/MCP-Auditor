"""Framework-agnostic domain representation of a discovered MCP tool.

``ToolProfile`` is intentionally decoupled from persistence (see
app.models.mcp_server_tool.MCPServerTool for the DB row) so the future
auditing engine (Phase 3+) can operate on plain domain objects regardless
of where they came from (live discovery, manual configuration, fixtures in
tests, etc).
"""

from typing import Any

from pydantic import BaseModel, ConfigDict


class ToolAnnotations(BaseModel):
    """MCP ``ToolAnnotations`` hints (untrusted - servers may misreport these)."""

    model_config = ConfigDict(extra="ignore")

    title: str | None = None
    read_only_hint: bool | None = None
    destructive_hint: bool | None = None
    idempotent_hint: bool | None = None
    open_world_hint: bool | None = None


class ToolProfile(BaseModel):
    """Normalized representation of a single MCP tool."""

    model_config = ConfigDict(extra="ignore")

    name: str
    title: str | None = None
    description: str | None = None
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] | None = None
    annotations: ToolAnnotations | None = None

    # Populated by the auditing engine in later phases; empty/neutral here.
    capabilities: list[str] = []
    side_effect_level: str | None = None
    risk_metadata: dict[str, Any] = {}
