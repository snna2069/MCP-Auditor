"""Audits tool input/output JSON Schemas for validity and clarity."""

from typing import Any

from app.auditors.base import BaseAuditor
from app.models.enums import AuditCategory, Severity
from app.schemas.audit_finding import AuditFinding
from app.schemas.tool_profile import ToolProfile


class SchemaAuditor(BaseAuditor):
    category = AuditCategory.TOOL_DEFINITION_QUALITY

    def audit(self, tool: ToolProfile) -> list[AuditFinding]:
        findings: list[AuditFinding] = []
        schema = tool.input_schema or {}

        if schema.get("type") != "object":
            findings.append(
                self._finding(
                    tool,
                    severity=Severity.MEDIUM,
                    title="Tool input schema is missing or malformed",
                    description=(
                        f"Tool '{tool.name}' does not declare an object-typed input "
                        "schema, so its accepted parameters cannot be validated."
                    ),
                    recommendation=(
                        "Define inputSchema as a JSON Schema object with a 'properties' map."
                    ),
                    evidence={"input_schema": schema},
                )
            )
            return findings  # remaining checks assume an object schema

        properties = schema.get("properties")
        properties = properties if isinstance(properties, dict) else {}

        untyped = sorted(name for name, prop in properties.items() if not _has_type(prop))
        if untyped:
            findings.append(
                self._finding(
                    tool,
                    severity=Severity.MEDIUM,
                    title="Tool schema has ambiguous parameters",
                    description=(
                        f"Tool '{tool.name}' has parameter(s) with no declared type: "
                        f"{', '.join(untyped)}. Callers cannot know what values are valid."
                    ),
                    recommendation="Add an explicit JSON Schema 'type' for every parameter.",
                    evidence={"parameters": untyped},
                )
            )

        undocumented = sorted(
            name for name, prop in properties.items() if not _has_description(prop)
        )
        if undocumented:
            findings.append(
                self._finding(
                    tool,
                    severity=Severity.LOW,
                    title="Tool schema parameters are undocumented",
                    description=(
                        f"Tool '{tool.name}' has parameter(s) with no description: "
                        f"{', '.join(undocumented)}."
                    ),
                    recommendation=(
                        "Add a 'description' for every parameter explaining its purpose."
                    ),
                    evidence={"parameters": undocumented},
                )
            )

        required = schema.get("required")
        required = required if isinstance(required, list) else []
        missing_required = sorted(name for name in required if name not in properties)
        if missing_required:
            findings.append(
                self._finding(
                    tool,
                    severity=Severity.MEDIUM,
                    title="Tool schema lists required parameters that are not defined",
                    description=(
                        f"Tool '{tool.name}' marks {', '.join(missing_required)} as "
                        "required, but they are not defined in 'properties'."
                    ),
                    recommendation=(
                        "Ensure every required parameter is also defined in 'properties'."
                    ),
                    evidence={"missing_required": missing_required},
                )
            )

        output_schema = tool.output_schema
        if output_schema is not None and output_schema.get("type") != "object":
            findings.append(
                self._finding(
                    tool,
                    severity=Severity.LOW,
                    title="Tool output schema is malformed",
                    description=(
                        f"Tool '{tool.name}' declares an outputSchema that is not an "
                        "object-typed JSON Schema."
                    ),
                    recommendation="Define outputSchema as a JSON Schema object, or omit it.",
                    evidence={"output_schema": output_schema},
                )
            )

        return findings


def _has_type(prop: Any) -> bool:
    return isinstance(prop, dict) and bool(prop.get("type"))


def _has_description(prop: Any) -> bool:
    return isinstance(prop, dict) and bool(prop.get("description"))
