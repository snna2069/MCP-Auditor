"""Pydantic schemas for the tool-discovery API surface."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import DiscoveryStatus
from app.schemas.tool_profile import ToolAnnotations


class ToolProfileRead(BaseModel):
    """A persisted, discovered tool as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    title: str | None
    description: str | None
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] | None
    annotations: ToolAnnotations | None
    discovered_at: datetime


class DiscoveryResult(BaseModel):
    """Outcome of a single discovery attempt against an MCP server."""

    status: DiscoveryStatus
    error: str | None = None
    discovered_at: datetime
    tool_count: int
    tools: list[ToolProfileRead]
