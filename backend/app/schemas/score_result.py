"""Framework-agnostic domain representation of a risk-scoring outcome.

Produced by app.scoring.risk_scorer.RiskScorer from a list of AuditFinding.
Decoupled from persistence for the same reasons as ToolProfile/AuditFinding;
Phase 5 will persist overall_score/risk_level onto the Audit record.
"""

from pydantic import BaseModel, ConfigDict

from app.models.enums import AuditCategory, RiskLevel, Severity


class ScoreContributor(BaseModel):
    """Explains exactly how much a single finding contributed to the score.

    Exists so the API can answer "why did this server receive a score of
    62?" by returning these alongside the overall score, per the project's
    "no black-box scoring" requirement.
    """

    model_config = ConfigDict(extra="ignore")

    tool_name: str
    category: AuditCategory
    severity: Severity
    title: str
    severity_weight: float
    category_weight: float
    contribution: float


class ScoreResult(BaseModel):
    """The full, explainable output of scoring a set of AuditFindings."""

    model_config = ConfigDict(extra="ignore")

    overall_score: float
    risk_level: RiskLevel
    category_scores: dict[AuditCategory, float]
    severity_breakdown: dict[Severity, int]
    score_contributors: list[ScoreContributor]
