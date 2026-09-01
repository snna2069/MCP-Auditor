"""MCP server registration endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import MCPServerNotFoundError
from app.models.mcp_server import MCPServer
from app.schemas.mcp_server import MCPServerCreate, MCPServerRead
from app.services.mcp_server_service import MCPServerService

router = APIRouter(prefix="/servers", tags=["servers"])


def _to_read_schema(server: MCPServer) -> MCPServerRead:
    return MCPServerRead(
        id=server.id,
        name=server.name,
        source_type=server.source_type,
        connection_config=MCPServerService.decrypt_connection_config(server),
        created_at=server.created_at,
        updated_at=server.updated_at,
    )


@router.post("", response_model=MCPServerRead, status_code=status.HTTP_201_CREATED)
def create_server(payload: MCPServerCreate, db: Session = Depends(get_db)) -> MCPServerRead:
    service = MCPServerService(db)
    server = service.create_server(payload)
    return _to_read_schema(server)


@router.get("", response_model=list[MCPServerRead])
def list_servers(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> list[MCPServerRead]:
    service = MCPServerService(db)
    servers = service.list_servers(skip=skip, limit=limit)
    return [_to_read_schema(server) for server in servers]


@router.get("/{server_id}", response_model=MCPServerRead)
def get_server(server_id: uuid.UUID, db: Session = Depends(get_db)) -> MCPServerRead:
    service = MCPServerService(db)
    try:
        server = service.get_server(server_id)
    except MCPServerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_read_schema(server)


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server(server_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    service = MCPServerService(db)
    try:
        service.delete_server(server_id)
    except MCPServerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
