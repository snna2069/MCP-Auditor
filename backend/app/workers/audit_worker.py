"""Celery task that runs the audit pipeline (Phase 5).

Runs in a separate worker process in production, so it opens its own DB
session rather than using FastAPI's request-scoped `get_db` dependency.
Imports `database` as a module (not `from ... import SessionLocal`) so
tests can monkeypatch `database.SessionLocal` and have this task pick up
the patched value even when Celery executes it eagerly, in-process.
"""

import logging
import uuid

from app.core import database
from app.services.audit_execution_service import AuditExecutionService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="execute_audit")
def execute_audit_task(audit_id: str) -> None:
    db = database.SessionLocal()
    try:
        AuditExecutionService(db).run_audit(uuid.UUID(audit_id))
    finally:
        db.close()
