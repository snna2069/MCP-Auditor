"""API response schemas for the persisted Audit / AuditFinding (Phase 5)."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import AuditCategory, AuditStatus, RiskLevel, Severity
from app.schemas.score_result import ScoreContributor


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


class AuditDetailRead(AuditRead):
    """AuditRead plus the full explainable score breakdown.

    category_scores/severity_breakdown/score_contributors are not persisted
    columns - they're recomputed from the audit's persisted AuditFinding
    rows at request time (RiskScorer is a pure function), so they can never
    drift from the findings actually stored. None while the audit has not
    completed (no findings/score exist yet, or it failed before scoring).
    """

    category_scores: dict[AuditCategory, float] | None
    severity_breakdown: dict[Severity, int] | None
    score_contributors: list[ScoreContributor] | None


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
