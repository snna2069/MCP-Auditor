"""Declarative base and shared model utilities.

Domain models added in later phases (``MCPServer``, ``Audit``,
``AuditFinding``, etc.) should inherit from ``Base`` so Alembic can discover
them for autogeneration.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""


# Imported at the bottom (after Base is defined) so submodules can `from
# app.models import Base`, and so Base.metadata is populated with every
# table for Alembic autogeneration / `create_all` in tests.
from app.models.mcp_server import MCPServer  # noqa: E402,F401
