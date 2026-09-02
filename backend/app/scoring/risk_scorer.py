"""Converts AuditFindings into an explainable score (Phase 4)."""

from collections.abc import Iterable

from app.models.enums import AuditCategory, Severity
from app.schemas.audit_finding import AuditFinding
from app.schemas.score_result import ScoreContributor, ScoreResult
from app.scoring.config import ScoringConfig, get_scoring_config


class RiskScorer:
    """Pure, deterministic scorer: same findings + config -> same result."""

    def __init__(self, config: ScoringConfig | None = None) -> None:
        self._config = config or get_scoring_config()

    def score(self, findings: list[AuditFinding]) -> ScoreResult:
        contributors = [self._contributor_for(finding) for finding in findings]

        overall_score = self._apply_deductions(c.contribution for c in contributors)

        category_scores = {
            category: self._apply_deductions(
                c.contribution for c in contributors if c.category == category
            )
            for category in AuditCategory
        }

        severity_breakdown = dict.fromkeys(Severity, 0)
        for finding in findings:
            severity_breakdown[finding.severity] += 1

        return ScoreResult(
            overall_score=overall_score,
            risk_level=self._config.classify(overall_score),
            category_scores=category_scores,
            severity_breakdown=severity_breakdown,
            score_contributors=sorted(contributors, key=lambda c: c.contribution, reverse=True),
        )

    def _apply_deductions(self, contributions: Iterable[float]) -> float:
        total_deduction = sum(contributions)
        return max(0.0, round(self._config.baseline_score - total_deduction, 2))

    def _contributor_for(self, finding: AuditFinding) -> ScoreContributor:
        severity_weight = self._config.severity_weight(finding.severity)
        category_weight = self._config.category_weight(finding.category)
        return ScoreContributor(
            tool_name=finding.tool_name,
            category=finding.category,
            severity=finding.severity,
            title=finding.title,
            severity_weight=severity_weight,
            category_weight=category_weight,
            contribution=round(severity_weight * category_weight, 2),
        )
