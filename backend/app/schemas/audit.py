"""API response schemas for the persisted Audit / AuditFinding (Phase 5)."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import AuditCategory, AuditStatus, RiskLevel, Severity


class AuditRead(BaseModel):
    """A persisted audit execution as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    server_id: uuid.UUID
    status: AuditStatus
    audit_version: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    overall_score: float | None
    risk_level: RiskLevel | None
    error_message: str | None


class AuditFindingRead(BaseModel):
    """A persisted audit finding as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    audit_id: uuid.UUID
    category: AuditCategory
    severity: Severity
    title: str
    description: str
    evidence: dict[str, Any]
    recommendation: str
    tool_name: str
    created_at: datetime
