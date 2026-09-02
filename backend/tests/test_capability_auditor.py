"""Tests for CapabilityAuditor."""

from app.auditors.capability_auditor import CapabilityAuditor
from app.models.enums import Severity
from app.schemas.tool_profile import ToolAnnotations, ToolProfile

auditor = CapabilityAuditor()


def test_flags_unrestricted_command_input() -> None:
    tool = ToolProfile(
        name="run_shell_command",
        description="Executes a shell command.",
        input_schema={"type": "object", "properties": {"command": {"type": "string"}}},
    )

    findings = auditor.audit(tool)

    matching = [f for f in findings if f.title == "Tool accepts unrestricted command input"]
    assert len(matching) == 1
    assert matching[0].severity == Severity.CRITICAL


def test_does_not_flag_constrained_command_input() -> None:
    tool = ToolProfile(
        name="run_shell_command",
        description="Executes one of a fixed set of shell commands.",
        input_schema={
            "type": "object",
            "properties": {"command": {"type": "string", "enum": ["ls", "pwd"]}},
        },
    )

    findings = auditor.audit(tool)

    assert not any(f.title == "Tool accepts unrestricted command input" for f in findings)


def test_flags_shell_and_network_combination() -> None:
    tool = ToolProfile(
        name="run_shell_command",
        description="Executes a shell command and posts the result via http.",
        input_schema={
            "type": "object",
            "properties": {"command": {"type": "string", "enum": ["ls"]}},
        },
    )

    findings = auditor.audit(tool)

    combo_findings = [
        f for f in findings if f.title == "Tool combines multiple high-risk capabilities"
    ]
    assert any("shell execution and network access" in f.description for f in combo_findings)


def test_flags_read_only_annotation_mismatch() -> None:
    tool = ToolProfile(
        name="delete_file",
        description="Deletes a file from disk.",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        annotations=ToolAnnotations(read_only_hint=True),
    )

    findings = auditor.audit(tool)

    matching = [
        f for f in findings if f.title == "Tool annotations claim read-only but appear destructive"
    ]
    assert len(matching) == 1
    assert matching[0].severity == Severity.CRITICAL


def test_benign_read_only_tool_produces_info_finding() -> None:
    tool = ToolProfile(
        name="get_weather",
        description="Get the current weather for a location.",
        input_schema={"type": "object", "properties": {"location": {"type": "string"}}},
        annotations=ToolAnnotations(read_only_hint=True),
    )

    findings = auditor.audit(tool)

    assert len(findings) == 1
    assert findings[0].title == "No elevated capabilities detected"
    assert findings[0].severity == Severity.INFO
