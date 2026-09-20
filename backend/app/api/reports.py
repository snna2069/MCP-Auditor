"""Audit report endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AuditIncompleteError, AuditNotFoundError
from app.schemas.report import AuditReport
from app.services.report_pdf_renderer import render_audit_report_pdf
from app.services.report_renderer import render_audit_report_html
from app.services.report_service import ReportService

router = APIRouter(tags=["reports"])


@router.get("/audits/{audit_id}/report", response_model=AuditReport)
def get_audit_report(audit_id: uuid.UUID, db: Session = Depends(get_db)) -> AuditReport:
    return _load_report(audit_id, db)


@router.get("/audits/{audit_id}/report/html", response_class=HTMLResponse)
def get_audit_report_html(audit_id: uuid.UUID, db: Session = Depends(get_db)) -> HTMLResponse:
    report = _load_report(audit_id, db)
    return HTMLResponse(content=render_audit_report_html(report), media_type="text/html")


@router.get("/audits/{audit_id}/report/pdf")
def get_audit_report_pdf(audit_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    report = _load_report(audit_id, db)
    return Response(
        content=render_audit_report_pdf(report),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="audit-{audit_id}.pdf"'},
    )


def _load_report(audit_id: uuid.UUID, db: Session) -> AuditReport:
    try:
        return ReportService(db).build_audit_report(audit_id)
    except AuditNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AuditIncompleteError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
