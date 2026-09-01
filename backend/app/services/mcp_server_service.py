"""Business logic for MCPServer registration and retrieval."""

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import MCPServerNotFoundError
from app.core.security import decrypt_json, encrypt_json
from app.models.mcp_server import MCPServer
from app.repositories.mcp_server_repository import MCPServerRepository
from app.schemas.mcp_server import MCPServerCreate


class MCPServerService:
    def __init__(self, db: Session) -> None:
        self._repo = MCPServerRepository(db)

    def create_server(self, payload: MCPServerCreate) -> MCPServer:
        server = MCPServer(
            name=payload.name,
            source_type=payload.source_type,
            connection_config_encrypted=encrypt_json(payload.connection_config),
        )
        return self._repo.add(server)

    def get_server(self, server_id: uuid.UUID) -> MCPServer:
        server = self._repo.get(server_id)
        if server is None:
            raise MCPServerNotFoundError(server_id)
        return server

    def list_servers(self, *, skip: int = 0, limit: int = 100) -> list[MCPServer]:
        return self._repo.list(skip=skip, limit=limit)

    def delete_server(self, server_id: uuid.UUID) -> None:
        server = self.get_server(server_id)
        self._repo.delete(server)

    @staticmethod
    def decrypt_connection_config(server: MCPServer) -> dict:
        return decrypt_json(server.connection_config_encrypted)
