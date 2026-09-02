"""Pydantic schemas for MCPServer registration and retrieval.

Each supported ``SourceType`` has its own connection-config shape. Rather
than requiring API clients to duplicate the source type inside
``connection_config`` (as a discriminator field would), ``MCPServerCreate``
validates the shape against the sibling ``source_type`` field via a model
validator. This keeps the wire format flat and simple:

    {"name": "...", "source_type": "HTTP", "connection_config": {"url": "..."}}
"""

import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.models.enums import SUPPORTED_SOURCE_TYPES, DiscoveryStatus, SourceType


class LocalCommandConfig(BaseModel):
    """Config for a server launched via a local command.

    Storing this configuration does not execute it; command execution is
    out of scope until a later phase.
    """

    model_config = ConfigDict(extra="forbid")

    command: str = Field(min_length=1)
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)


class HttpConfig(BaseModel):
    """Config for a server reachable over HTTP."""

    model_config = ConfigDict(extra="forbid")

    url: HttpUrl
    headers: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: Annotated[int, Field(gt=0, le=300)] = 30


class ManualConfig(BaseModel):
    """Freeform config for servers described manually (no live connection)."""

    model_config = ConfigDict(extra="forbid")

    description: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


_CONFIG_BY_SOURCE_TYPE: dict[SourceType, type[BaseModel]] = {
    SourceType.LOCAL_COMMAND: LocalCommandConfig,
    SourceType.HTTP: HttpConfig,
    SourceType.MANUAL_CONFIGURATION: ManualConfig,
}


class MCPServerCreate(BaseModel):
    """Payload for registering a new MCP server."""

    name: str = Field(min_length=1, max_length=255)
    source_type: SourceType
    connection_config: dict[str, Any]

    @model_validator(mode="after")
    def _validate_connection_config(self) -> "MCPServerCreate":
        if self.source_type not in SUPPORTED_SOURCE_TYPES:
            supported = ", ".join(sorted(t.value for t in SUPPORTED_SOURCE_TYPES))
            raise ValueError(
                f"source_type '{self.source_type.value}' is not supported yet. "
                f"Supported types: {supported}."
            )

        config_model = _CONFIG_BY_SOURCE_TYPE[self.source_type]
        # Re-validate/normalize connection_config against the schema for this
        # source_type, then store the normalized dict back so downstream
        # code (encryption, persistence) always sees a consistent shape.
        validated = config_model.model_validate(self.connection_config)
        self.connection_config = validated.model_dump(mode="json")
        return self


class MCPServerRead(BaseModel):
    """Representation of a persisted MCP server returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    source_type: SourceType
    connection_config: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    last_discovery_status: DiscoveryStatus | None = None
    last_discovered_at: datetime | None = None
    last_discovery_error: str | None = None
