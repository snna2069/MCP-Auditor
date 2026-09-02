"""Tests for DescriptionAuditor."""

from app.auditors.description_auditor import DescriptionAuditor
from app.models.enums import Severity
from app.schemas.tool_profile import ToolAnnotations, ToolProfile

auditor = DescriptionAuditor()


def test_flags_missing_description() -> None:
    tool = ToolProfile(name="mystery_tool", description=None, input_schema={"type": "object"})

    findings = auditor.audit(tool)

    titles = [f.title for f in findings]
    assert "Tool has no description" in titles


def test_flags_brief_description() -> None:
    tool = ToolProfile(name="search", description="Searches.", input_schema={"type": "object"})

    findings = auditor.audit(tool)

    assert any(f.title == "Tool description is too brief" for f in findings)


def test_flags_destructive_name_without_disclosure() -> None:
    tool = ToolProfile(
        name="delete_file",
        description="Deletes a file from disk.",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
    )

    findings = auditor.audit(tool)

    matching = [
        f for f in findings if f.title == "Tool description does not disclose destructive behavior"
    ]
    assert len(matching) == 1
    assert matching[0].severity == Severity.HIGH


def test_does_not_flag_destructive_name_when_disclosed() -> None:
    tool = ToolProfile(
        name="delete_file",
        description="Permanently deletes a file from disk. This action cannot be undone.",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
    )

    findings = auditor.audit(tool)

    assert not any(
        f.title == "Tool description does not disclose destructive behavior" for f in findings
    )


def test_flags_annotation_destructive_hint_without_disclosure() -> None:
    tool = ToolProfile(
        name="cleanup",
        description="Cleans up temporary state used by the workflow.",
        input_schema={"type": "object"},
        annotations=ToolAnnotations(destructive_hint=True),
    )

    findings = auditor.audit(tool)

    assert any(
        f.title == "Tool description does not disclose destructive behavior" for f in findings
    )


def test_benign_tool_produces_no_findings() -> None:
    tool = ToolProfile(
        name="get_weather",
        description="Get the current weather conditions for a given location.",
        input_schema={"type": "object", "properties": {"location": {"type": "string"}}},
    )

    findings = auditor.audit(tool)

    assert findings == []
