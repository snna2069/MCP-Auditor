"""Framework-agnostic domain representation of a single audit finding.

Produced by auditors (app.auditors.*) operating on a ToolProfile. This is
intentionally decoupled from persistence: Phase 5 will introduce the
persisted Audit/AuditFinding tables (with id/audit_id/created_at) that wrap
these once a full audit run is triggered and stored.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import AuditCategory, Severity


class AuditFinding(BaseModel):
    """A single, specific issue identified by an auditor."""

    model_config = ConfigDict(extra="ignore")

    category: AuditCategory
    severity: Severity
    title: str
    description: str
    evidence: dict[str, Any] = {}
    recommendation: str
    tool_name: str
