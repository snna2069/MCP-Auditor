"""Tests for SchemaAuditor."""

from app.auditors.schema_auditor import SchemaAuditor
from app.schemas.tool_profile import ToolProfile

auditor = SchemaAuditor()


def test_flags_missing_object_schema() -> None:
    tool = ToolProfile(name="broken", description="A tool.", input_schema={})

    findings = auditor.audit(tool)

    assert len(findings) == 1
    assert findings[0].title == "Tool input schema is missing or malformed"


def test_flags_ambiguous_untyped_parameter() -> None:
    tool = ToolProfile(
        name="search",
        description="Searches records.",
        input_schema={"type": "object", "properties": {"query": {"description": "The query"}}},
    )

    findings = auditor.audit(tool)

    titles = [f.title for f in findings]
    assert "Tool schema has ambiguous parameters" in titles


def test_flags_undocumented_parameter() -> None:
    tool = ToolProfile(
        name="search",
        description="Searches records.",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
    )

    findings = auditor.audit(tool)

    titles = [f.title for f in findings]
    assert "Tool schema parameters are undocumented" in titles


def test_flags_required_parameter_not_defined() -> None:
    tool = ToolProfile(
        name="search",
        description="Searches records.",
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "q"}},
            "required": ["query", "limit"],
        },
    )

    findings = auditor.audit(tool)

    titles = [f.title for f in findings]
    assert "Tool schema lists required parameters that are not defined" in titles


def test_flags_malformed_output_schema() -> None:
    tool = ToolProfile(
        name="search",
        description="Searches records.",
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "q"}},
        },
        output_schema={"foo": "bar"},
    )

    findings = auditor.audit(tool)

    titles = [f.title for f in findings]
    assert "Tool output schema is malformed" in titles


def test_well_formed_schema_produces_no_findings() -> None:
    tool = ToolProfile(
        name="search",
        description="Searches records.",
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query"}},
            "required": ["query"],
        },
        output_schema={"type": "object", "properties": {"results": {"type": "array"}}},
    )

    findings = auditor.audit(tool)

    assert findings == []
