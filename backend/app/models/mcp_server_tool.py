"""MCPServerTool ORM model.

Persisted, normalized snapshot of a tool discovered from an MCPServer (see
app.mcp for the protocol clients that produce this data, and
app.schemas.tool_profile.ToolProfile for the framework-agnostic domain
representation used by the auditing engine).
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class MCPServerTool(Base):
    __tablename__ = "mcp_server_tools"
    __table_args__ = (
        UniqueConstraint("server_id", "name", name="uq_mcp_server_tools_server_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mcp_servers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_schema: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    output_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    annotations: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<MCPServerTool id={self.id} server_id={self.server_id} name={self.name!r}>"
