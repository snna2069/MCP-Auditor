"""Tool-discovery endpoints for a registered MCP server."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import MCPServerNotFoundError
from app.schemas.discovery import DiscoveryResult, ToolProfileRead
from app.services.mcp_discovery_service import MCPDiscoveryService

router = APIRouter(prefix="/servers/{server_id}", tags=["discovery"])


@router.post("/discover", response_model=DiscoveryResult)
def discover_server(server_id: uuid.UUID, db: Session = Depends(get_db)) -> DiscoveryResult:
    """Connect to the server, discover its tools, and persist the result.

    Always returns 200: the response body's ``status`` field reports
    whether the discovery attempt itself succeeded or failed (e.g. the
    server was unreachable). A 404 is only returned if the MCPServer
    record does not exist.
    """
    service = MCPDiscoveryService(db)
    try:
        server, tools = service.discover(server_id)
    except MCPServerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return DiscoveryResult(
        status=server.last_discovery_status,
        error=server.last_discovery_error,
        discovered_at=server.last_discovered_at,
        tool_count=len(tools),
        tools=[ToolProfileRead.model_validate(tool) for tool in tools],
    )


@router.get("/tools", response_model=list[ToolProfileRead])
def list_server_tools(server_id: uuid.UUID, db: Session = Depends(get_db)) -> list[ToolProfileRead]:
    """Return the most recently discovered tools for a server (no live call)."""
    service = MCPDiscoveryService(db)
    try:
        tools = service.list_tools(server_id)
    except MCPServerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [ToolProfileRead.model_validate(tool) for tool in tools]
