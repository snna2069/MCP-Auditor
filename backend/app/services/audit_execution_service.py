"""Runs the full audit pipeline for a single Audit (Phase 5).

This is the worker-side orchestration invoked by the Celery task
(app.workers.audit_worker). app.services.audit_service is the thin,
API-facing layer that creates Audit rows and enqueues this.

Pipeline: load server -> discover MCP capabilities -> normalize tools ->
run auditors -> collect findings -> calculate score -> persist results ->
mark audit complete.
"""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.auditors.registry import run_auditors
from app.models.audit import Audit
from app.models.enums import AuditStatus, DiscoveryStatus
from app.repositories.audit_finding_repository import AuditFindingRepository
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit_finding import AuditFinding
from app.scoring.risk_scorer import RiskScorer
from app.services.mcp_discovery_service import MCPDiscoveryService, tool_profile_from_row

logger = logging.getLogger(__name__)


class AuditExecutionService:
    def __init__(self, db: Session) -> None:
        self._audit_repo = AuditRepository(db)
        self._finding_repo = AuditFindingRepository(db)
        self._discovery_service = MCPDiscoveryService(db)
        self._scorer = RiskScorer()

    def run_audit(self, audit_id: uuid.UUID) -> None:
        """Execute the full pipeline for ``audit_id``.

        Never raises: any failure, expected or not, is recorded on the
        Audit row (status=FAILED, sanitized error_message) rather than
        propagated, so a worker/task failure can never crash the caller
        (important both for a real Celery worker and for Celery's eager
        test mode, where .delay() runs in-process).
        """
        try:
            self._run(audit_id)
        except Exception:
            logger.exception("unrecoverable error running audit", extra={"audit_id": str(audit_id)})

    def _run(self, audit_id: uuid.UUID) -> None:
        audit = self._audit_repo.get(audit_id)
        if audit is None:
            logger.error("audit not found, cannot execute", extra={"audit_id": str(audit_id)})
            return

        audit.status = AuditStatus.RUNNING
        audit.started_at = datetime.now(UTC)
        self._audit_repo.save(audit)

        try:
            server, tool_rows = self._discovery_service.discover(audit.server_id)

            if server.last_discovery_status == DiscoveryStatus.FAILED:
                self._fail(audit, server.last_discovery_error or "Tool discovery failed.")
                return

            tools = [tool_profile_from_row(row) for row in tool_rows]

            findings: list[AuditFinding] = []
            for tool in tools:
                findings.extend(run_auditors(tool))

            score = self._scorer.score(findings)

            self._finding_repo.add_all(audit.id, findings)

            audit.overall_score = score.overall_score
            audit.risk_level = score.risk_level
            audit.status = AuditStatus.COMPLETED
            audit.completed_at = datetime.now(UTC)
            self._audit_repo.save(audit)
        except Exception as exc:
            logger.exception("audit pipeline failed", extra={"audit_id": str(audit_id)})
            self._fail(
                audit,
                f"Audit failed due to an internal error ({type(exc).__name__}). "
                "See server logs for details.",
            )

    def _fail(self, audit: Audit, error_message: str) -> None:
        audit.status = AuditStatus.FAILED
        audit.completed_at = datetime.now(UTC)
        audit.error_message = error_message
        self._audit_repo.save(audit)
