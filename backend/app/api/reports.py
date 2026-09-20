"""Audit report endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AuditIncompleteError, AuditNotFoundError
from app.schemas.report import AuditReport
from app.services.report_service import ReportService

router = APIRouter(tags=["reports"])


@router.get("/audits/{audit_id}/report", response_model=AuditReport)
def get_audit_report(audit_id: uuid.UUID, db: Session = Depends(get_db)) -> AuditReport:
    try:
        return ReportService(db).build_audit_report(audit_id)
    except AuditNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AuditIncompleteError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
