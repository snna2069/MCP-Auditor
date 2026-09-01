"""Declarative base and shared model utilities.

Domain models added in later phases (``MCPServer``, ``Audit``,
``AuditFinding``, etc.) should inherit from ``Base`` so Alembic can discover
them for autogeneration.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""
