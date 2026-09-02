"""Discovery for MANUAL_CONFIGURATION servers.

There is no live connection to make; tools are read directly from the
freeform ``details`` the user supplied when registering the server. If
``details["tools"]`` is present, each entry is expected to follow the MCP
``Tool`` shape (``name``, ``description``, ``inputSchema``, ...). Malformed
entries are skipped with a warning rather than failing the whole
discovery, since manual configs are user-authored and may be incomplete.
"""

from typing import Any

from app.mcp.base import MCPClient, MCPDiscoveryResult
from app.mcp.wire_models import parse_tool


class ManualMCPClient(MCPClient):
    def __init__(self, connection_config: dict[str, Any]) -> None:
        self._details = connection_config.get("details") or {}

    def discover(self) -> MCPDiscoveryResult:
        raw_tools = self._details.get("tools") if isinstance(self._details, dict) else None
        tools = []
        warnings: list[str] = []

        if isinstance(raw_tools, list):
            for index, raw_tool in enumerate(raw_tools):
                try:
                    tools.append(parse_tool(raw_tool))
                except (KeyError, TypeError) as exc:
                    warnings.append(f"Skipped tools[{index}]: {exc}")
        elif raw_tools is not None:
            warnings.append("'details.tools' was present but not a list; ignored.")

        return MCPDiscoveryResult(tools=tools, warnings=warnings)
