"""Direct tests for AuditExecutionService's failure handling."""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.audit import Audit
from app.models.enums import AuditStatus, SourceType
from app.models.mcp_server import MCPServer
from app.schemas.mcp_server import MCPServerCreate
from app.services.audit_execution_service import AuditExecutionService
from app.services.mcp_server_service import MCPServerService


def _create_server(db_session: Session) -> MCPServer:
    service = MCPServerService(db_session)
    payload = MCPServerCreate(
        name="unit-test-server",
        source_type=SourceType.MANUAL_CONFIGURATION,
        connection_config={"details": {"tools": []}},
    )
    return service.create_server(payload)


def _create_pending_audit(db_session: Session, server_id: uuid.UUID) -> Audit:
    audit = Audit(server_id=server_id, status=AuditStatus.PENDING, audit_version="test")
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)
    return audit


def test_run_audit_does_nothing_for_missing_audit(db_session: Session) -> None:
    service = AuditExecutionService(db_session)

    # Must not raise.
    service.run_audit(uuid.uuid4())


def test_run_audit_marks_failed_on_internal_error(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    server = _create_server(db_session)
    audit = _create_pending_audit(db_session, server.id)

    def _boom(self, findings):
        raise RuntimeError("sensitive internal detail that must not leak")

    monkeypatch.setattr("app.scoring.risk_scorer.RiskScorer.score", _boom)

    service = AuditExecutionService(db_session)
    service.run_audit(audit.id)

    db_session.refresh(audit)
    assert audit.status == AuditStatus.FAILED
    assert audit.error_message is not None
    assert "RuntimeError" in audit.error_message
    assert "sensitive internal detail" not in audit.error_message


def test_run_audit_completes_successfully_for_manual_server_with_no_tools(
    db_session: Session,
) -> None:
    server = _create_server(db_session)
    audit = _create_pending_audit(db_session, server.id)

    AuditExecutionService(db_session).run_audit(audit.id)

    db_session.refresh(audit)
    assert audit.status == AuditStatus.COMPLETED
    assert audit.overall_score == 100.0
