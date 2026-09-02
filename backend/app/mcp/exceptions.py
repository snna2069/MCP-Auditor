"""Errors raised by MCP protocol clients (app.mcp.*).

These are caught by app.services.mcp_discovery_service and turned into a
sanitized DiscoveryResult - never surfaced to the API as raw stack traces.
"""


class MCPClientError(Exception):
    """Base class for all MCP client errors."""


class MCPConnectionError(MCPClientError):
    """Raised when a transport-level connection could not be established."""


class MCPTimeoutError(MCPClientError):
    """Raised when the server did not respond within the configured timeout."""


class MCPProtocolError(MCPClientError):
    """Raised when the server returned an invalid or JSON-RPC error response."""
