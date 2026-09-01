"""Data-access layer for MCPServer. No business logic lives here."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mcp_server import MCPServer


class MCPServerRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, server: MCPServer) -> MCPServer:
        self._db.add(server)
        self._db.commit()
        self._db.refresh(server)
        return server

    def get(self, server_id: uuid.UUID) -> MCPServer | None:
        return self._db.get(MCPServer, server_id)

    def list(self, *, skip: int = 0, limit: int = 100) -> list[MCPServer]:
        stmt = select(MCPServer).order_by(MCPServer.created_at.desc()).offset(skip).limit(limit)
        return list(self._db.scalars(stmt).all())

    def delete(self, server: MCPServer) -> None:
        self._db.delete(server)
        self._db.commit()
