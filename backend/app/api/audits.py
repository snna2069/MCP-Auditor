"""Audit execution endpoints (Phase 5)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AuditNotFoundError, MCPServerNotFoundError
from app.schemas.audit import AuditDetailRead, AuditFindingRead, AuditRead
from app.services.audit_service import AuditService

router = APIRouter(tags=["audits"])


@router.post(
    "/servers/{server_id}/audits",
    response_model=AuditRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_audit(server_id: uuid.UUID, db: Session = Depends(get_db)) -> AuditRead:
    """Trigger an audit. Runs asynchronously - poll GET /audits/{id} for results."""
    service = AuditService(db)
    try:
        audit = service.create_audit(server_id)
    except MCPServerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AuditRead.model_validate(audit)


@router.get("/audits", response_model=list[AuditRead])
def list_audits(
    server_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[AuditRead]:
    service = AuditService(db)
    audits = service.list_audits(server_id=server_id, skip=skip, limit=limit)
    return [AuditRead.model_validate(audit) for audit in audits]


@router.get("/audits/{audit_id}", response_model=AuditDetailRead)
def get_audit(audit_id: uuid.UUID, db: Session = Depends(get_db)) -> AuditDetailRead:
    service = AuditService(db)
    try:
        audit, score = service.get_audit_with_score(audit_id)
    except AuditNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return AuditDetailRead(
        **AuditRead.model_validate(audit).model_dump(),
        category_scores=score.category_scores if score else None,
        severity_breakdown=score.severity_breakdown if score else None,
        score_contributors=score.score_contributors if score else None,
    )


@router.get("/audits/{audit_id}/findings", response_model=list[AuditFindingRead])
def list_audit_findings(
    audit_id: uuid.UUID, db: Session = Depends(get_db)
) -> list[AuditFindingRead]:
    service = AuditService(db)
    try:
        findings = service.list_findings(audit_id)
    except AuditNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [AuditFindingRead.model_validate(finding) for finding in findings]
