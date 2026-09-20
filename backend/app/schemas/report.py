"""Stable JSON response models for completed audit reports."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    AuditCategory,
    AuditStatus,
    DiscoveryStatus,
    RiskLevel,
    Severity,
    SourceType,
)
from app.schemas.score_result import ScoreContributor


class ReportMetadata(BaseModel):
    schema_version: str
    report_timestamp: datetime


class ReportServer(BaseModel):
    id: uuid.UUID
    name: str
    source_type: SourceType
    created_at: datetime
    updated_at: datetime
    last_discovery_status: DiscoveryStatus | None
    last_discovered_at: datetime | None


class ReportFinding(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: AuditCategory
    severity: Severity
    title: str
    description: str
    evidence: dict[str, Any]
    recommendation: str
    tool_name: str
    created_at: datetime


class AuditReport(BaseModel):
    report_metadata: ReportMetadata
    server: ReportServer
    audit_id: uuid.UUID
    audit_version: str
    status: AuditStatus
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    overall_score: float
    risk_level: RiskLevel
    category_scores: dict[AuditCategory, float]
    severity_breakdown: dict[Severity, int]
    score_contributors: list[ScoreContributor]
    findings: list[ReportFinding]
