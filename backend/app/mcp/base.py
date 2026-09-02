"""Abstract base for MCP protocol clients."""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from app.schemas.tool_profile import ToolProfile


class MCPDiscoveryResult(BaseModel):
    """Raw discovery outcome from a client, before persistence."""

    server_name: str | None = None
    server_version: str | None = None
    protocol_version: str | None = None
    tools: list[ToolProfile] = []
    warnings: list[str] = []


class MCPClient(ABC):
    """Connects to an MCP server and discovers its available tools.

    Implementations must raise ``app.mcp.exceptions.MCPClientError``
    subclasses on failure rather than letting transport-specific exceptions
    (e.g. ``httpx.HTTPError``, ``OSError``) escape, so callers have one
    error hierarchy to handle.
    """

    @abstractmethod
    def discover(self) -> MCPDiscoveryResult:
        """Connect, perform the MCP handshake, and list available tools."""
