"""Data-access layer for MCPServerTool. No business logic lives here."""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.mcp_server_tool import MCPServerTool


class MCPServerToolRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_server(self, server_id: uuid.UUID) -> list[MCPServerTool]:
        stmt = (
            select(MCPServerTool)
            .where(MCPServerTool.server_id == server_id)
            .order_by(MCPServerTool.name)
        )
        return list(self._db.scalars(stmt).all())

    def replace_all(self, server_id: uuid.UUID, tools: list[MCPServerTool]) -> list[MCPServerTool]:
        """Atomically replace the persisted tool snapshot for a server."""
        self._db.execute(delete(MCPServerTool).where(MCPServerTool.server_id == server_id))
        for tool in tools:
            tool.server_id = server_id
            self._db.add(tool)
        self._db.commit()
        return self.list_by_server(server_id)
