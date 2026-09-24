"""Builds stable reports from persisted audit results."""

import logging
import time
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import AuditIncompleteError, AuditNotFoundError
from app.core.observability import correlation_fields, elapsed, metrics
from app.models.audit_finding import AuditFinding as AuditFindingRow
from app.models.enums import AuditStatus
from app.repositories.audit_finding_repository import AuditFindingRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.mcp_server_repository import MCPServerRepository
from app.schemas.audit_finding import AuditFinding
from app.schemas.report import AuditReport, ReportFinding, ReportMetadata, ReportServer
from app.scoring.risk_scorer import RiskScorer

logger = logging.getLogger(__name__)

REPORT_SCHEMA_VERSION = "1"


class ReportService:
    def __init__(self, db: Session) -> None:
        self._audit_repo = AuditRepository(db)
        self._finding_repo = AuditFindingRepository(db)
        self._server_repo = MCPServerRepository(db)
        self._scorer = RiskScorer()

    def build_audit_report(self, audit_id: uuid.UUID) -> AuditReport:
        started = time.monotonic()
        logger.info("report generation started", extra=correlation_fields(audit_id=audit_id))
        audit = self._audit_repo.get(audit_id)
        if audit is None:
            raise AuditNotFoundError(audit_id)
        if audit.status != AuditStatus.COMPLETED:
            raise AuditIncompleteError(audit_id)
        if audit.overall_score is None or audit.risk_level is None:
            raise AuditIncompleteError(audit_id)

        server = self._server_repo.get(audit.server_id)
        if server is None:  # The foreign key normally makes this impossible.
            raise AuditIncompleteError(audit_id)

        rows = self._finding_repo.list_by_audit(audit.id)
        findings = [_to_domain_finding(row) for row in rows]
        breakdown = self._scorer.score(findings)

        report = AuditReport(
            report_metadata=ReportMetadata(
                schema_version=REPORT_SCHEMA_VERSION,
                report_timestamp=audit.completed_at or audit.created_at,
            ),
            server=ReportServer(
                id=server.id,
                name=server.name,
                source_type=server.source_type,
                created_at=server.created_at,
                updated_at=server.updated_at,
                last_discovery_status=server.last_discovery_status,
                last_discovered_at=server.last_discovered_at,
            ),
            audit_id=audit.id,
            audit_version=audit.audit_version,
            status=audit.status,
            created_at=audit.created_at,
            started_at=audit.started_at,
            completed_at=audit.completed_at,
            overall_score=audit.overall_score,
            risk_level=audit.risk_level,
            category_scores=breakdown.category_scores,
            severity_breakdown=breakdown.severity_breakdown,
            score_contributors=breakdown.score_contributors,
            findings=[ReportFinding.model_validate(row) for row in rows],
        )
        metrics.increment("reports_generated_total")
        metrics.observe("report_generation_duration_seconds", elapsed(started))
        logger.info(
            "report generation completed",
            extra=correlation_fields(audit_id=audit_id, duration_seconds=elapsed(started)),
        )
        return report


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
