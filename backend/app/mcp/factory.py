"""Dispatches to the correct MCPClient implementation by source type.

Keeps app.services.mcp_discovery_service decoupled from the concrete
client classes.
"""

from typing import Any

from app.mcp.base import MCPClient
from app.mcp.exceptions import MCPClientError
from app.mcp.http_client import HttpMCPClient
from app.mcp.manual_client import ManualMCPClient
from app.mcp.stdio_client import StdioMCPClient
from app.models.enums import SourceType


def build_mcp_client(
    source_type: SourceType, connection_config: dict[str, Any], *, timeout: float
) -> MCPClient:
    if source_type == SourceType.LOCAL_COMMAND:
        return StdioMCPClient(
            command=connection_config["command"],
            args=connection_config.get("args", []),
            env=connection_config.get("env", {}),
            timeout=timeout,
        )
    if source_type == SourceType.HTTP:
        return HttpMCPClient(
            url=connection_config["url"],
            headers=connection_config.get("headers", {}),
            timeout=connection_config.get("timeout_seconds", timeout),
        )
    if source_type == SourceType.MANUAL_CONFIGURATION:
        return ManualMCPClient(connection_config)

    raise MCPClientError(f"Discovery is not supported for source type '{source_type.value}'.")
