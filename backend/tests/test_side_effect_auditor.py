"""Tests for SideEffectAuditor, mirroring the examples in PROJECT_PLAN.md."""

from app.auditors.side_effect_auditor import SideEffectAuditor
from app.models.enums import Severity
from app.schemas.tool_profile import ToolAnnotations, ToolProfile

auditor = SideEffectAuditor()


def _level(tool: ToolProfile) -> str:
    findings = auditor.audit(tool)
    assert len(findings) == 1
    return findings[0].evidence["side_effect_level"]


def test_search_operation_is_none_or_low() -> None:
    tool = ToolProfile(
        name="search_docs",
        description="Search internal documentation for a query.",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
        annotations=ToolAnnotations(read_only_hint=True),
    )

    assert _level(tool) in {"NONE", "LOW"}


def test_create_database_record_is_moderate() -> None:
    tool = ToolProfile(
        name="create_database_record",
        description="Creates a new record in the database.",
        input_schema={
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Target table"},
                "data": {"type": "object", "description": "Row data"},
            },
        },
    )

    assert _level(tool) == "MODERATE"


def test_send_email_is_high() -> None:
    tool = ToolProfile(
        name="send_email",
        description="Sends an email notification to a recipient.",
        input_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient address"},
                "subject": {"type": "string", "description": "Email subject"},
            },
        },
    )

    assert _level(tool) == "HIGH"


def test_delete_cloud_resources_is_critical() -> None:
    tool = ToolProfile(
        name="delete_cloud_resources",
        description=(
            "Permanently deletes cloud infrastructure resources. This action cannot be undone."
        ),
        input_schema={
            "type": "object",
            "properties": {"resource_id": {"type": "string", "description": "Resource to delete"}},
        },
    )

    findings = auditor.audit(tool)

    assert findings[0].evidence["side_effect_level"] == "CRITICAL"
    assert findings[0].severity == Severity.CRITICAL
