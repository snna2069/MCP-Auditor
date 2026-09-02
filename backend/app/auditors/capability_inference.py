"""Deterministic, heuristic capability inference for MCP tools.

MCP does not give clients a formal "capabilities" field for a Tool - only
best-effort ToolAnnotations hints, which servers may misreport. This module
infers *likely* capabilities from keyword signals in the tool's name,
description, and input schema, to flag tools for human review. It is not
proof of ground truth (see app.auditors.keywords for the determinism
rationale).

Deliberately, an annotation claiming READ_ONLY and keyword evidence of
DESTRUCTIVE_OPERATION/SHELL_EXECUTION are allowed to coexist in the result:
that contradiction is exactly the signal CapabilityAuditor uses to flag a
tool that may be hiding destructive behavior.
"""

from typing import Any

from app.auditors import keywords as kw
from app.models.enums import Capability
from app.schemas.tool_profile import ToolProfile

CapabilityEvidence = dict[Capability, list[str]]

_KEYWORD_CAPABILITY_MAP: dict[Capability, frozenset[str]] = {
    Capability.SHELL_EXECUTION: kw.SHELL_EXECUTION_KEYWORDS,
    Capability.NETWORK: kw.NETWORK_KEYWORDS,
    Capability.FILE_SYSTEM: kw.FILE_SYSTEM_KEYWORDS,
    Capability.DATABASE: kw.DATABASE_KEYWORDS,
    Capability.SECRETS_ACCESS: kw.SECRETS_KEYWORDS,
    Capability.IDENTITY_ACCESS: kw.IDENTITY_KEYWORDS,
    Capability.INFRASTRUCTURE: kw.INFRASTRUCTURE_KEYWORDS,
    Capability.DESTRUCTIVE_OPERATION: kw.DESTRUCTIVE_KEYWORDS,
}

_WRITE_LIKE_CAPABILITIES = frozenset(
    {Capability.DATA_WRITE, Capability.DESTRUCTIVE_OPERATION, Capability.SHELL_EXECUTION}
)


def infer_capabilities(tool: ToolProfile) -> tuple[set[Capability], CapabilityEvidence]:
    """Infer a tool's capability tags and the keyword evidence for each."""
    haystack = _build_haystack(tool)
    capabilities: set[Capability] = set()
    evidence: CapabilityEvidence = {}

    for capability, keyword_set in _KEYWORD_CAPABILITY_MAP.items():
        matched = kw.find_matches(haystack, keyword_set)
        if matched:
            capabilities.add(capability)
            evidence[capability] = matched

    annotations = tool.annotations
    if annotations and annotations.destructive_hint is True:
        capabilities.add(Capability.DESTRUCTIVE_OPERATION)
        evidence.setdefault(Capability.DESTRUCTIVE_OPERATION, []).append(
            "annotations.destructiveHint=true"
        )

    if Capability.DESTRUCTIVE_OPERATION not in capabilities:
        matched_write = kw.find_matches(haystack, kw.WRITE_KEYWORDS)
        if matched_write:
            capabilities.add(Capability.DATA_WRITE)
            evidence[Capability.DATA_WRITE] = matched_write

    is_read_only_annotated = bool(annotations and annotations.read_only_hint is True)
    has_write_like_capability = bool(capabilities & _WRITE_LIKE_CAPABILITIES)

    if is_read_only_annotated:
        capabilities.add(Capability.READ_ONLY)
        evidence.setdefault(Capability.READ_ONLY, []).append("annotations.readOnlyHint=true")
    elif not has_write_like_capability:
        matched_read = kw.find_matches(haystack, kw.READ_ONLY_KEYWORDS)
        if matched_read:
            capabilities.add(Capability.READ_ONLY)
            evidence[Capability.READ_ONLY] = matched_read

    return capabilities, evidence


def _build_haystack(tool: ToolProfile) -> str:
    parts = [tool.name, tool.description or ""]
    properties = _schema_properties(tool.input_schema)
    for prop_name, prop_schema in properties.items():
        parts.append(prop_name)
        if isinstance(prop_schema, dict):
            parts.append(str(prop_schema.get("description") or ""))
    return kw.normalize(" ".join(parts))


def _schema_properties(schema: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(schema, dict):
        return {}
    properties = schema.get("properties")
    return properties if isinstance(properties, dict) else {}
