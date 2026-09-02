"""Wire-format constants and normalization for MCP protocol messages.

Parses raw ``initialize``/``tools/list`` results (per the MCP 2025-06-18
schema) into the framework-agnostic ``ToolProfile`` domain object.
"""

from typing import Any

from app.schemas.tool_profile import ToolAnnotations, ToolProfile

# Latest protocol version this client negotiates. If a server responds with
# a different (older) version it supports, we accept it as-is per spec
# ("If the client does not support the version in the server's response, it
# SHOULD disconnect") - MCP servers are expected to be backwards compatible
# within a major revision, and Phase 2 only reads tool metadata.
PROTOCOL_VERSION = "2025-06-18"

CLIENT_NAME = "mcp-server-auditor"
CLIENT_VERSION = "0.1.0"

CLIENT_INFO = {"name": CLIENT_NAME, "title": "MCP Server Auditor", "version": CLIENT_VERSION}

INITIALIZE_PARAMS = {
    "protocolVersion": PROTOCOL_VERSION,
    "capabilities": {},
    "clientInfo": CLIENT_INFO,
}


def parse_tool(raw: dict[str, Any]) -> ToolProfile:
    """Normalize a single raw MCP ``Tool`` object into a ``ToolProfile``."""
    annotations_raw = raw.get("annotations")
    annotations = None
    if isinstance(annotations_raw, dict):
        annotations = ToolAnnotations(
            title=annotations_raw.get("title"),
            read_only_hint=annotations_raw.get("readOnlyHint"),
            destructive_hint=annotations_raw.get("destructiveHint"),
            idempotent_hint=annotations_raw.get("idempotentHint"),
            open_world_hint=annotations_raw.get("openWorldHint"),
        )

    return ToolProfile(
        name=raw["name"],
        title=raw.get("title"),
        description=raw.get("description"),
        input_schema=raw.get("inputSchema") or {"type": "object"},
        output_schema=raw.get("outputSchema"),
        annotations=annotations,
    )


def parse_tools(raw_tools: list[dict[str, Any]]) -> list[ToolProfile]:
    return [parse_tool(tool) for tool in raw_tools]
