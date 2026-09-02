"""Tests for RiskScorer: determinism, explainability, configurability."""

from app.models.enums import AuditCategory, RiskLevel, Severity
from app.schemas.audit_finding import AuditFinding
from app.scoring.config import ScoringConfig
from app.scoring.risk_scorer import RiskScorer


def _finding(
    category: AuditCategory = AuditCategory.CAPABILITY_PERMISSION_RISK,
    severity: Severity = Severity.HIGH,
    title: str = "finding",
    tool_name: str = "some_tool",
) -> AuditFinding:
    return AuditFinding(
        category=category,
        severity=severity,
        title=title,
        description="description",
        recommendation="recommendation",
        tool_name=tool_name,
    )


def test_no_findings_yields_baseline_score_and_lowest_risk() -> None:
    result = RiskScorer().score([])

    assert result.overall_score == 100.0
    assert result.risk_level == RiskLevel.LOW
    assert result.score_contributors == []
    assert all(count == 0 for count in result.severity_breakdown.values())
    assert all(score == 100.0 for score in result.category_scores.values())


def test_info_findings_do_not_reduce_score() -> None:
    result = RiskScorer().score([_finding(severity=Severity.INFO)])

    assert result.overall_score == 100.0


def test_single_critical_finding_reduces_score_by_configured_weight() -> None:
    config = ScoringConfig()
    result = RiskScorer(config).score([_finding(severity=Severity.CRITICAL)])

    expected_deduction = config.severity_weight(Severity.CRITICAL) * config.category_weight(
        AuditCategory.CAPABILITY_PERMISSION_RISK
    )
    assert result.overall_score == 100.0 - expected_deduction


def test_score_never_drops_below_zero() -> None:
    findings = [_finding(severity=Severity.CRITICAL, title=f"f{i}") for i in range(20)]

    result = RiskScorer().score(findings)

    assert result.overall_score == 0.0
    assert result.risk_level == RiskLevel.CRITICAL


def test_category_scores_are_independent_per_category() -> None:
    findings = [
        _finding(category=AuditCategory.SIDE_EFFECT_ANALYSIS, severity=Severity.CRITICAL),
        _finding(category=AuditCategory.TOOL_DEFINITION_QUALITY, severity=Severity.INFO),
    ]

    result = RiskScorer().score(findings)

    assert result.category_scores[AuditCategory.TOOL_DEFINITION_QUALITY] == 100.0
    assert result.category_scores[AuditCategory.SIDE_EFFECT_ANALYSIS] < 100.0


def test_severity_breakdown_counts_match_input() -> None:
    findings = [
        _finding(severity=Severity.HIGH, title="a"),
        _finding(severity=Severity.HIGH, title="b"),
        _finding(severity=Severity.LOW, title="c"),
    ]

    result = RiskScorer().score(findings)

    assert result.severity_breakdown[Severity.HIGH] == 2
    assert result.severity_breakdown[Severity.LOW] == 1
    assert result.severity_breakdown[Severity.CRITICAL] == 0


def test_score_contributors_are_explainable_and_sum_to_the_deduction() -> None:
    findings = [
        _finding(severity=Severity.HIGH, title="a"),
        _finding(severity=Severity.MEDIUM, title="b"),
    ]

    result = RiskScorer().score(findings)

    assert len(result.score_contributors) == 2
    total_contribution = sum(c.contribution for c in result.score_contributors)
    assert result.overall_score == 100.0 - total_contribution
    # Sorted descending, so the HIGH finding's larger contribution comes first.
    assert result.score_contributors[0].title == "a"


def test_score_contributors_reference_originating_tool_and_finding() -> None:
    finding = _finding(severity=Severity.HIGH, title="dangerous", tool_name="run_shell")

    result = RiskScorer().score([finding])

    contributor = result.score_contributors[0]
    assert contributor.tool_name == "run_shell"
    assert contributor.title == "dangerous"
    assert contributor.category == AuditCategory.CAPABILITY_PERMISSION_RISK
    assert contributor.severity == Severity.HIGH


def test_custom_config_changes_scoring_deterministically() -> None:
    findings = [_finding(severity=Severity.HIGH)]

    default_result = RiskScorer(ScoringConfig()).score(findings)
    lenient_result = RiskScorer(ScoringConfig(severity_weights={Severity.HIGH: 1.0})).score(
        findings
    )

    assert lenient_result.overall_score > default_result.overall_score


def test_category_weight_amplifies_deduction() -> None:
    findings = [_finding(severity=Severity.HIGH, category=AuditCategory.SIDE_EFFECT_ANALYSIS)]

    baseline_result = RiskScorer(ScoringConfig()).score(findings)
    amplified_result = RiskScorer(
        ScoringConfig(category_weights={AuditCategory.SIDE_EFFECT_ANALYSIS: 3.0})
    ).score(findings)

    assert amplified_result.overall_score < baseline_result.overall_score


def test_scoring_is_deterministic_across_repeated_runs() -> None:
    findings = [
        _finding(severity=Severity.CRITICAL, title="a"),
        _finding(severity=Severity.MEDIUM, category=AuditCategory.SIDE_EFFECT_ANALYSIS, title="b"),
    ]
    scorer = RiskScorer()

    first = scorer.score(findings)
    second = scorer.score(findings)

    assert first == second
