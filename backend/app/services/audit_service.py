"""API-facing audit service: create/list/get audits and their findings.

Thin by design - the actual pipeline logic lives in
app.services.audit_execution_service.AuditExecutionService, run by the
Celery worker this service enqueues into.
"""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.auditors.registry import AUDITOR_ENGINE_VERSION
from app.core.exceptions import AuditNotFoundError
from app.models.audit import Audit
from app.models.audit_finding import AuditFinding as AuditFindingRow
from app.models.enums import AuditStatus
from app.repositories.audit_finding_repository import AuditFindingRepository
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit_finding import AuditFinding
from app.schemas.score_result import ScoreResult
from app.scoring.risk_scorer import RiskScorer
from app.services.mcp_server_service import MCPServerService
from app.workers.audit_worker import execute_audit_task

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, db: Session) -> None:
        self._server_service = MCPServerService(db)
        self._audit_repo = AuditRepository(db)
        self._finding_repo = AuditFindingRepository(db)
        self._scorer = RiskScorer()

    def create_audit(self, server_id: uuid.UUID) -> Audit:
        # Raises MCPServerNotFoundError (propagated to the API as 404) if
        # the server doesn't exist.
        self._server_service.get_server(server_id)

        audit = Audit(
            server_id=server_id,
            status=AuditStatus.PENDING,
            audit_version=AUDITOR_ENGINE_VERSION,
        )
        audit = self._audit_repo.create(audit)

        try:
            execute_audit_task.delay(str(audit.id))
        except Exception:
            # Enqueueing itself failed (e.g. broker/Redis unreachable) -
            # fail the audit immediately rather than leaving it stuck
            # PENDING forever or letting this HTTP request hang retrying
            # the broker connection.
            logger.exception("failed to enqueue audit task", extra={"audit_id": str(audit.id)})
            audit.status = AuditStatus.FAILED
            audit.completed_at = datetime.now(UTC)
            audit.error_message = (
                "Could not start the audit: the background worker/broker is "
                "unavailable. Please try again shortly."
            )
            return self._audit_repo.save(audit)

        # If the task already ran synchronously (Celery eager mode, used in
        # tests), pick up its committed changes; a no-op in real async use.
        return self._audit_repo.refresh(audit)

    def get_audit(self, audit_id: uuid.UUID) -> Audit:
        audit = self._audit_repo.get(audit_id)
        if audit is None:
            raise AuditNotFoundError(audit_id)
        return audit

    def get_audit_with_score(self, audit_id: uuid.UUID) -> tuple[Audit, ScoreResult | None]:
        """Fetch an audit plus its full score breakdown.

        The breakdown is recomputed from persisted findings rather than
        stored, so it can never drift from what's actually in the DB. None
        if the audit hasn't completed (no findings/score exist yet).
        """
        audit = self.get_audit(audit_id)
        if audit.status != AuditStatus.COMPLETED:
            return audit, None

        rows = self._finding_repo.list_by_audit(audit_id)
        findings = [_to_domain_finding(row) for row in rows]
        return audit, self._scorer.score(findings)

    def list_audits(
        self,
        *,
        server_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Audit]:
        return self._audit_repo.list(server_id=server_id, skip=skip, limit=limit)

    def list_findings(self, audit_id: uuid.UUID) -> list[AuditFindingRow]:
        self.get_audit(audit_id)  # raises AuditNotFoundError if missing
        return self._finding_repo.list_by_audit(audit_id)


def _to_domain_finding(row: AuditFindingRow) -> AuditFinding:
    return AuditFinding(
        category=row.category,
        severity=row.severity,
        title=row.title,
        description=row.description,
        evidence=row.evidence,
        recommendation=row.recommendation,
        tool_name=row.tool_name,
    )
