"""MCPServer ORM model.

Represents a registered MCP server configuration to be audited.
``connection_config`` is stored encrypted (see app.core.security) because it
may contain secrets such as auth headers or command environment variables;
the service layer is responsible for encrypting/decrypting it.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base
from app.models.enums import DiscoveryStatus, SourceType


class MCPServer(Base):
    __tablename__ = "mcp_servers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="mcp_server_source_type", native_enum=False, length=50),
        nullable=False,
    )
    # Encrypted (Fernet) JSON blob of the connection configuration.
    connection_config_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Populated by the discovery service (app.services.mcp_discovery_service).
    # last_discovery_error is a sanitized, human-readable message only -
    # never a raw exception/stack trace, to avoid leaking connection
    # secrets or internal infrastructure details.
    last_discovery_status: Mapped[DiscoveryStatus | None] = mapped_column(
        Enum(
            DiscoveryStatus,
            name="mcp_server_discovery_status",
            native_enum=False,
            length=20,
        ),
        nullable=True,
    )
    last_discovered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_discovery_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<MCPServer id={self.id} name={self.name!r} source_type={self.source_type}>"
