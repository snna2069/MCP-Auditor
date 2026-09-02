"""Orchestrates MCP tool discovery: connect, normalize, persist.

Deliberately thin - protocol details live in app.mcp, persistence details
live in the repositories. This service just wires them together and
translates client failures into a sanitized, persisted outcome.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.mcp.exceptions import MCPClientError
from app.mcp.factory import build_mcp_client
from app.models.enums import DiscoveryStatus
from app.models.mcp_server import MCPServer
from app.models.mcp_server_tool import MCPServerTool
from app.repositories.mcp_server_tool_repository import MCPServerToolRepository
from app.schemas.tool_profile import ToolProfile
from app.services.mcp_server_service import MCPServerService


class MCPDiscoveryService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._server_service = MCPServerService(db)
        self._tool_repo = MCPServerToolRepository(db)

    def discover(self, server_id: uuid.UUID) -> tuple[MCPServer, list[MCPServerTool]]:
        """Run discovery for a server, persist the outcome, and return it.

        Raises MCPServerNotFoundError (propagated from the server service)
        if the server does not exist. Client/protocol failures are caught
        and recorded on the server rather than raised, since a failed
        discovery is still a well-defined, successful API response.
        """
        server = self._server_service.get_server(server_id)
        connection_config = MCPServerService.decrypt_connection_config(server)
        settings = get_settings()

        try:
            client = build_mcp_client(
                server.source_type,
                connection_config,
                timeout=settings.mcp_discovery_timeout_seconds,
            )
            result = client.discover()
        except MCPClientError as exc:
            server.last_discovery_status = DiscoveryStatus.FAILED
            server.last_discovered_at = datetime.now(UTC)
            server.last_discovery_error = str(exc)
            self._db.commit()
            return server, self._tool_repo.list_by_server(server_id)

        rows = [_to_row(profile) for profile in _dedupe_by_name(result.tools)]
        persisted = self._tool_repo.replace_all(server_id, rows)

        server.last_discovery_status = DiscoveryStatus.SUCCESS
        server.last_discovered_at = datetime.now(UTC)
        server.last_discovery_error = None
        self._db.commit()

        return server, persisted

    def list_tools(self, server_id: uuid.UUID) -> list[MCPServerTool]:
        # Raises MCPServerNotFoundError if the server doesn't exist.
        self._server_service.get_server(server_id)
        return self._tool_repo.list_by_server(server_id)


def _to_row(profile: ToolProfile) -> MCPServerTool:
    return MCPServerTool(
        name=profile.name,
        title=profile.title,
        description=profile.description,
        input_schema=profile.input_schema,
        output_schema=profile.output_schema,
        annotations=(profile.annotations.model_dump(mode="json") if profile.annotations else None),
    )


def _dedupe_by_name(tools: list[ToolProfile]) -> list[ToolProfile]:
    """Keep the first occurrence of each tool name.

    Servers are untrusted; a misbehaving one could report duplicate names,
    which would otherwise violate the (server_id, name) uniqueness we rely
    on to keep discovery snapshots simple.
    """
    seen: set[str] = set()
    deduped = []
    for tool in tools:
        if tool.name in seen:
            continue
        seen.add(tool.name)
        deduped.append(tool)
    return deduped
