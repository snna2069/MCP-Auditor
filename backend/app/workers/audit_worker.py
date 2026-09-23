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
from app.core.observability import correlation_fields, metrics
from app.services.audit_execution_service import AuditExecutionService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="execute_audit")
def execute_audit_task(audit_id: str) -> None:
    logger.info("audit worker started", extra=correlation_fields(audit_id=audit_id))
    db = database.SessionLocal()
    try:
        AuditExecutionService(db).run_audit(uuid.UUID(audit_id))
    except Exception as exc:
        metrics.increment("worker_failures_total", reason=type(exc).__name__)
        logger.exception(
            "audit worker failed",
            extra=correlation_fields(audit_id=audit_id, failure_reason=type(exc).__name__),
        )
        raise
    finally:
        db.close()
        logger.info("audit worker finished", extra=correlation_fields(audit_id=audit_id))
