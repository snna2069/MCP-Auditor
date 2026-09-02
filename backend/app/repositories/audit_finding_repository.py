"""Data-access layer for AuditFinding. No business logic lives here."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_finding import AuditFinding as AuditFindingRow
from app.schemas.audit_finding import AuditFinding


class AuditFindingRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add_all(self, audit_id: uuid.UUID, findings: list[AuditFinding]) -> list[AuditFindingRow]:
        rows = [
            AuditFindingRow(
                audit_id=audit_id,
                category=finding.category,
                severity=finding.severity,
                title=finding.title,
                description=finding.description,
                evidence=finding.evidence,
                recommendation=finding.recommendation,
                tool_name=finding.tool_name,
            )
            for finding in findings
        ]
        self._db.add_all(rows)
        self._db.commit()
        return rows

    def list_by_audit(self, audit_id: uuid.UUID) -> list[AuditFindingRow]:
        stmt = (
            select(AuditFindingRow)
            .where(AuditFindingRow.audit_id == audit_id)
            .order_by(AuditFindingRow.created_at)
        )
        return list(self._db.scalars(stmt).all())
