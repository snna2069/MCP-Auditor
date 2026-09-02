"""Centralized, config-driven scoring parameters.

This is the single place risk-scoring numbers (baseline, per-severity
deductions, per-category weights, risk-level thresholds) are defined. Per
the project's requirement to avoid hardcoded risk scores scattered through
the app, everything that influences a score must be read from a
``ScoringConfig`` instance rather than inlined in auditors/services.

Note: unlike app.core.config.Settings, this is not sourced from environment
variables - the weight maps are nested and best expressed/reviewed as code.
"""

from functools import lru_cache

from pydantic import BaseModel, ConfigDict

from app.models.enums import AuditCategory, RiskLevel, Severity


class ScoringConfig(BaseModel):
    """All tunable parameters for RiskScorer."""

    model_config = ConfigDict(frozen=True)

    # Every score starts here and only ever goes down (see RiskScorer).
    baseline_score: float = 100.0

    # Points deducted per finding of a given severity, before category weighting.
    severity_weights: dict[Severity, float] = {
        Severity.INFO: 0.0,
        Severity.LOW: 2.0,
        Severity.MEDIUM: 5.0,
        Severity.HIGH: 15.0,
        Severity.CRITICAL: 30.0,
    }

    # Multiplier applied on top of the severity weight, per audit dimension.
    # All dimensions are weighted equally by default; tune here, not in
    # auditor code, if some categories should matter more to the overall score.
    category_weights: dict[AuditCategory, float] = {category: 1.0 for category in AuditCategory}

    # Checked in order; the first threshold the score is >= wins. Must
    # remain sorted descending and end in 0.0 so classify() always matches.
    risk_level_thresholds: tuple[tuple[float, RiskLevel], ...] = (
        (90.0, RiskLevel.LOW),
        (70.0, RiskLevel.MODERATE),
        (40.0, RiskLevel.HIGH),
        (0.0, RiskLevel.CRITICAL),
    )

    def severity_weight(self, severity: Severity) -> float:
        return self.severity_weights.get(severity, 0.0)

    def category_weight(self, category: AuditCategory) -> float:
        return self.category_weights.get(category, 1.0)

    def classify(self, score: float) -> RiskLevel:
        for threshold, level in self.risk_level_thresholds:
            if score >= threshold:
                return level
        # Unreachable as long as risk_level_thresholds ends in 0.0, which is
        # enforced by the default above; kept as a defensive fallback for
        # custom configs that omit a zero floor.
        return self.risk_level_thresholds[-1][1]


@lru_cache
def get_scoring_config() -> ScoringConfig:
    """Return the cached, default ScoringConfig.

    Tests/callers that need different weights should construct their own
    ScoringConfig(...) and pass it to RiskScorer directly rather than
    mutating this shared instance.
    """
    return ScoringConfig()
