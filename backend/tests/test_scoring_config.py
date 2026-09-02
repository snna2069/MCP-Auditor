"""Tests for ScoringConfig - the centralized, non-hardcoded scoring numbers."""

from app.models.enums import AuditCategory, RiskLevel, Severity
from app.scoring.config import ScoringConfig, get_scoring_config


def test_default_config_has_zero_weight_for_info() -> None:
    config = get_scoring_config()
    assert config.severity_weight(Severity.INFO) == 0.0


def test_default_config_thresholds_are_sorted_descending_and_end_at_zero() -> None:
    config = get_scoring_config()
    thresholds = [t for t, _ in config.risk_level_thresholds]

    assert thresholds == sorted(thresholds, reverse=True)
    assert thresholds[-1] == 0.0


def test_classify_matches_documented_boundaries() -> None:
    config = get_scoring_config()

    assert config.classify(100) == RiskLevel.LOW
    assert config.classify(90) == RiskLevel.LOW
    assert config.classify(89.99) == RiskLevel.MODERATE
    assert config.classify(70) == RiskLevel.MODERATE
    assert config.classify(69.99) == RiskLevel.HIGH
    assert config.classify(40) == RiskLevel.HIGH
    assert config.classify(39.99) == RiskLevel.CRITICAL
    assert config.classify(0) == RiskLevel.CRITICAL


def test_unknown_category_falls_back_to_weight_one() -> None:
    config = ScoringConfig(category_weights={})
    assert config.category_weight(AuditCategory.SIDE_EFFECT_ANALYSIS) == 1.0


def test_get_scoring_config_is_cached_singleton() -> None:
    assert get_scoring_config() is get_scoring_config()


def test_custom_config_is_independent_of_default() -> None:
    custom = ScoringConfig(baseline_score=50.0)
    default = get_scoring_config()

    assert custom.baseline_score == 50.0
    assert default.baseline_score == 100.0
