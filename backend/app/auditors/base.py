"""Abstract base for deterministic tool auditors."""

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from app.models.enums import AuditCategory, Severity
from app.schemas.audit_finding import AuditFinding
from app.schemas.tool_profile import ToolProfile


class BaseAuditor(ABC):
    """Analyzes a single ToolProfile and returns a list of AuditFinding.

    Implementations must be deterministic: the same ToolProfile must always
    produce the same findings.
    """

    category: ClassVar[AuditCategory]

    @abstractmethod
    def audit(self, tool: ToolProfile) -> list[AuditFinding]:
        """Perform this auditor's focused analysis on ``tool``."""

    def _finding(
        self,
        tool: ToolProfile,
        *,
        severity: Severity,
        title: str,
        description: str,
        recommendation: str,
        evidence: dict[str, Any] | None = None,
    ) -> AuditFinding:
        return AuditFinding(
            category=self.category,
            severity=severity,
            title=title,
            description=description,
            evidence=evidence or {},
            recommendation=recommendation,
            tool_name=tool.name,
        )
