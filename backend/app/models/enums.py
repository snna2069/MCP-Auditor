"""Domain enums shared by ORM models and Pydantic schemas."""

import enum


class SourceType(enum.StrEnum):
    """How an MCP server is connected to / located."""

    LOCAL_COMMAND = "LOCAL_COMMAND"
    HTTP = "HTTP"
    SSE = "SSE"
    PACKAGE = "PACKAGE"
    MANUAL_CONFIGURATION = "MANUAL_CONFIGURATION"


# Source types the ingestion API accepts as of Phase 1. SSE and PACKAGE are
# part of the long-term domain model but are not implemented yet.
SUPPORTED_SOURCE_TYPES: frozenset[SourceType] = frozenset(
    {
        SourceType.LOCAL_COMMAND,
        SourceType.HTTP,
        SourceType.MANUAL_CONFIGURATION,
    }
)


class DiscoveryStatus(enum.StrEnum):
    """Outcome of the most recent tool-discovery attempt for a server."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
