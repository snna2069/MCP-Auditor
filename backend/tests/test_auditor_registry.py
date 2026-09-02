"""Definition of done for Phase 3: a known set of sample MCP tools produces
deterministic findings when run through the full default auditor set.
"""

from app.auditors.registry import run_auditors
from app.models.enums import AuditCategory, Severity
from app.schemas.tool_profile import ToolAnnotations, ToolProfile

SAMPLE_TOOLS = {
    "delete_file": ToolProfile(
        name="delete_file",
        description="Deletes a file from disk.",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
    ),
    "get_weather": ToolProfile(
        name="get_weather",
        description="Get the current weather conditions for a given location.",
        input_schema={
            "type": "object",
            "properties": {"location": {"type": "string", "description": "City name"}},
            "required": ["location"],
        },
        annotations=ToolAnnotations(read_only_hint=True),
    ),
    "run_shell_command": ToolProfile(
        name="run_shell_command",
        description=("Executes a shell command and posts the result to a remote server via http."),
        input_schema={"type": "object", "properties": {"command": {"type": "string"}}},
    ),
}


def test_sample_tools_produce_identical_findings_across_runs() -> None:
    first_pass = {name: run_auditors(tool) for name, tool in SAMPLE_TOOLS.items()}
    second_pass = {name: run_auditors(tool) for name, tool in SAMPLE_TOOLS.items()}

    assert first_pass == second_pass


def test_delete_file_produces_expected_findings() -> None:
    findings = run_auditors(SAMPLE_TOOLS["delete_file"])
    titles = {f.title for f in findings}

    assert "Tool description does not disclose destructive behavior" in titles
    disclosure_finding = next(
        f for f in findings if f.title == "Tool description does not disclose destructive behavior"
    )
    assert disclosure_finding.severity == Severity.HIGH
    assert disclosure_finding.category == AuditCategory.TOOL_DEFINITION_QUALITY


def test_get_weather_produces_only_benign_findings() -> None:
    findings = run_auditors(SAMPLE_TOOLS["get_weather"])

    assert all(f.severity in {Severity.INFO, Severity.LOW} for f in findings)


def test_run_shell_command_produces_critical_findings() -> None:
    findings = run_auditors(SAMPLE_TOOLS["run_shell_command"])

    assert any(f.severity == Severity.CRITICAL for f in findings)
    assert any(f.title == "Tool accepts unrestricted command input" for f in findings)
    assert any(
        f.title == "Tool combines multiple high-risk capabilities"
        and "shell execution and network access" in f.description
        for f in findings
    )
