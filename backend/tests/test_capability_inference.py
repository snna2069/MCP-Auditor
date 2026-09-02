"""Tests for the keyword utilities and capability inference heuristics."""

from app.auditors.capability_inference import infer_capabilities
from app.auditors.keywords import find_matches, normalize
from app.models.enums import Capability
from app.schemas.tool_profile import ToolAnnotations, ToolProfile


def test_normalize_treats_underscores_and_hyphens_as_separators() -> None:
    assert normalize("Shell_Command-Runner") == "shell command runner"


def test_find_matches_requires_whole_token() -> None:
    # "get" must not match inside "budget".
    assert find_matches(normalize("budget_report"), frozenset({"get"})) == []
    assert find_matches(normalize("get_report"), frozenset({"get"})) == ["get"]


def test_infer_capabilities_shell_and_network() -> None:
    tool = ToolProfile(
        name="run_shell_command",
        description="Executes a shell command and posts the result via http.",
        input_schema={"type": "object", "properties": {"command": {"type": "string"}}},
    )

    capabilities, evidence = infer_capabilities(tool)

    assert Capability.SHELL_EXECUTION in capabilities
    assert Capability.NETWORK in capabilities
    assert "shell" in evidence[Capability.SHELL_EXECUTION]


def test_infer_capabilities_read_only_annotation_is_trusted_as_a_signal() -> None:
    tool = ToolProfile(
        name="get_weather",
        description="Get the current weather for a location.",
        input_schema={"type": "object", "properties": {"location": {"type": "string"}}},
        annotations=ToolAnnotations(read_only_hint=True),
    )

    capabilities, _ = infer_capabilities(tool)

    assert capabilities == {Capability.READ_ONLY}


def test_infer_capabilities_flags_contradiction_between_hint_and_keywords() -> None:
    tool = ToolProfile(
        name="delete_file",
        description="Deletes a file from disk.",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        annotations=ToolAnnotations(read_only_hint=True),
    )

    capabilities, _ = infer_capabilities(tool)

    # Both signals are kept - the contradiction itself is meaningful.
    assert Capability.READ_ONLY in capabilities
    assert Capability.DESTRUCTIVE_OPERATION in capabilities
