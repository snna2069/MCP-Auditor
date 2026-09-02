"""Data-access layer for Audit. No business logic lives here."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import Audit


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, audit: Audit) -> Audit:
        self._db.add(audit)
        self._db.commit()
        self._db.refresh(audit)
        return audit

    def get(self, audit_id: uuid.UUID) -> Audit | None:
        return self._db.get(Audit, audit_id)

    def list(
        self,
        *,
        server_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Audit]:
        stmt = select(Audit).order_by(Audit.created_at.desc()).offset(skip).limit(limit)
        if server_id is not None:
            stmt = stmt.where(Audit.server_id == server_id)
        return list(self._db.scalars(stmt).all())

    def save(self, audit: Audit) -> Audit:
        """Persist in-place changes to an already-tracked Audit."""
        self._db.commit()
        self._db.refresh(audit)
        return audit

    def refresh(self, audit: Audit) -> Audit:
        """Reload column values from the DB for an already-tracked Audit.

        Needed because in Celery's eager test mode, execute_audit_task runs
        synchronously via a *different* Session object (see
        app.workers.audit_worker) that commits its own changes to the same
        underlying database - this instance's in-memory copy would
        otherwise still show the pre-task state.
        """
        self._db.refresh(audit)
        return audit
