"""Tests for the Phase 6 security test harness (payload library + detector).

Definition of done: the system can evaluate known malicious or suspicious
tool-output scenarios and generate findings.
"""

import pytest

from app.models.enums import AuditCategory, SecurityTestCategory
from app.security.detector import PromptInjectionDetector
from app.security.payloads import DEFAULT_PAYLOADS

detector = PromptInjectionDetector()


@pytest.mark.parametrize("payload", DEFAULT_PAYLOADS, ids=[p.id for p in DEFAULT_PAYLOADS])
def test_payload_detection_matches_expectation(payload) -> None:
    findings = detector.scan(payload.payload, tool_name="test_tool")

    assert bool(findings) == payload.expected_detection, (
        f"payload {payload.id!r} expected_detection={payload.expected_detection} "
        f"but got {len(findings)} finding(s)"
    )


def test_every_category_has_at_least_one_malicious_and_one_benign_fixture() -> None:
    for category in SecurityTestCategory:
        matching = [p for p in DEFAULT_PAYLOADS if p.category == category]
        assert any(p.expected_detection for p in matching), (
            f"{category} has no malicious (expected_detection=True) fixture"
        )
        assert any(not p.expected_detection for p in matching), (
            f"{category} has no benign (expected_detection=False) fixture"
        )


def test_detected_findings_use_prompt_injection_risk_category() -> None:
    malicious = next(p for p in DEFAULT_PAYLOADS if p.expected_detection)

    findings = detector.scan(malicious.payload, tool_name="weather_tool")

    assert len(findings) >= 1
    assert all(f.category == AuditCategory.PROMPT_INJECTION_RISK for f in findings)
    assert all(f.tool_name == "weather_tool" for f in findings)


def test_finding_evidence_includes_matched_patterns_and_security_category() -> None:
    malicious = next(p for p in DEFAULT_PAYLOADS if p.id == "prompt_injection_ignore_previous")

    findings = detector.scan(malicious.payload)

    assert len(findings) == 1
    evidence = findings[0].evidence
    assert evidence["security_category"] == SecurityTestCategory.PROMPT_INJECTION.value
    assert evidence["matched_patterns"]


def test_empty_or_missing_text_produces_no_findings() -> None:
    assert detector.scan("") == []
    assert detector.scan(None) == []  # type: ignore[arg-type]


def test_scanning_is_deterministic() -> None:
    malicious = next(p for p in DEFAULT_PAYLOADS if p.expected_detection)

    first = detector.scan(malicious.payload, tool_name="t")
    second = detector.scan(malicious.payload, tool_name="t")

    assert first == second


def test_realistic_benign_json_tool_output_is_not_flagged() -> None:
    benign_output = '{"temperature": 22.5, "conditions": "Partly cloudy", "humidity": 65}'

    assert detector.scan(benign_output) == []
