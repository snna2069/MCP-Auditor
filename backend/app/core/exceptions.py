"""Framework-agnostic domain exceptions.

Services raise these; the API layer maps them to HTTP responses. Keeping
services free of FastAPI/HTTPException dependencies lets them be reused by
future workers or CLI tooling without pulling in the web framework.
"""


class DomainError(Exception):
    """Base class for domain-level errors."""


class MCPServerNotFoundError(DomainError):
    """Raised when a requested MCPServer does not exist."""

    def __init__(self, server_id: object) -> None:
        self.server_id = server_id
        super().__init__(f"MCP server '{server_id}' not found.")


class UnsupportedSourceTypeError(DomainError):
    """Raised when a server is created with a not-yet-supported source type."""

    def __init__(self, source_type: object) -> None:
        self.source_type = source_type
        super().__init__(f"Source type '{source_type}' is not supported yet.")
