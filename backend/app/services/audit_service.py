"""API-facing audit service: create/list/get audits and their findings.

Thin by design - the actual pipeline logic lives in
app.services.audit_execution_service.AuditExecutionService, run by the
Celery worker this service enqueues into.
"""

import uuid

from sqlalchemy.orm import Session

from app.auditors.registry import AUDITOR_ENGINE_VERSION
from app.core.exceptions import AuditNotFoundError
from app.models.audit import Audit
from app.models.audit_finding import AuditFinding as AuditFindingRow
from app.models.enums import AuditStatus
from app.repositories.audit_finding_repository import AuditFindingRepository
from app.repositories.audit_repository import AuditRepository
from app.services.mcp_server_service import MCPServerService
from app.workers.audit_worker import execute_audit_task


class AuditService:
    def __init__(self, db: Session) -> None:
        self._server_service = MCPServerService(db)
        self._audit_repo = AuditRepository(db)
        self._finding_repo = AuditFindingRepository(db)

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

        execute_audit_task.delay(str(audit.id))

        # If the task already ran synchronously (Celery eager mode, used in
        # tests), pick up its committed changes; a no-op in real async use.
        return self._audit_repo.refresh(audit)

    def get_audit(self, audit_id: uuid.UUID) -> Audit:
        audit = self._audit_repo.get(audit_id)
        if audit is None:
            raise AuditNotFoundError(audit_id)
        return audit

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
