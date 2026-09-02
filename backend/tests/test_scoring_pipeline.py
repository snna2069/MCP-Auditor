"""End-to-end: run auditors then score the findings, for known sample tools."""

from app.auditors.registry import run_auditors
from app.models.enums import RiskLevel
from app.schemas.tool_profile import ToolAnnotations, ToolProfile
from app.scoring.risk_scorer import RiskScorer

BENIGN_TOOL = ToolProfile(
    name="get_weather",
    description="Get the current weather conditions for a given location.",
    input_schema={
        "type": "object",
        "properties": {"location": {"type": "string", "description": "City name"}},
        "required": ["location"],
    },
    annotations=ToolAnnotations(read_only_hint=True),
)

DANGEROUS_TOOL = ToolProfile(
    name="run_shell_command",
    description=("Executes a shell command and posts the result to a remote server via http."),
    input_schema={"type": "object", "properties": {"command": {"type": "string"}}},
)


def test_benign_tool_scores_low_risk() -> None:
    findings = run_auditors(BENIGN_TOOL)
    result = RiskScorer().score(findings)

    assert result.risk_level == RiskLevel.LOW


def test_dangerous_tool_scores_high_or_critical_risk() -> None:
    findings = run_auditors(DANGEROUS_TOOL)
    result = RiskScorer().score(findings)

    assert result.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    assert result.overall_score < 100.0
    # The scoring output must be able to explain itself.
    assert len(result.score_contributors) == len(findings)


def test_scoring_pipeline_is_deterministic_end_to_end() -> None:
    first = RiskScorer().score(run_auditors(DANGEROUS_TOOL))
    second = RiskScorer().score(run_auditors(DANGEROUS_TOOL))

    assert first == second
