"""Classifies a tool's expected side effects (NONE..CRITICAL)."""

from app.auditors.base import BaseAuditor
from app.auditors.capability_inference import infer_capabilities
from app.models.enums import AuditCategory, Capability, Severity, SideEffectLevel
from app.schemas.audit_finding import AuditFinding
from app.schemas.tool_profile import ToolProfile

_LEVEL_TO_SEVERITY = {
    SideEffectLevel.NONE: Severity.INFO,
    SideEffectLevel.LOW: Severity.INFO,
    SideEffectLevel.MODERATE: Severity.LOW,
    SideEffectLevel.HIGH: Severity.HIGH,
    SideEffectLevel.CRITICAL: Severity.CRITICAL,
}

_HIGH_IMPACT_RESOURCES = frozenset(
    {Capability.DATABASE, Capability.INFRASTRUCTURE, Capability.FILE_SYSTEM}
)
_OUTBOUND_COMMUNICATION = frozenset({Capability.DATA_WRITE, Capability.IDENTITY_ACCESS})


class SideEffectAuditor(BaseAuditor):
    category = AuditCategory.SIDE_EFFECT_ANALYSIS

    def audit(self, tool: ToolProfile) -> list[AuditFinding]:
        capabilities, evidence = infer_capabilities(tool)
        level, reasons = _classify(tool, capabilities)

        keyword_evidence = {c.value: evidence[c] for c in capabilities if c in evidence}

        return [
            self._finding(
                tool,
                severity=_LEVEL_TO_SEVERITY[level],
                title=f"Tool side effect level: {level.value}",
                description=(
                    f"Tool '{tool.name}' is classified as {level.value} side effect "
                    f"({'; '.join(reasons)})."
                ),
                recommendation=_recommendation_for(level),
                evidence={
                    "side_effect_level": level.value,
                    "capabilities": sorted(c.value for c in capabilities),
                    "keyword_evidence": keyword_evidence,
                },
            )
        ]


def _classify(
    tool: ToolProfile, capabilities: set[Capability]
) -> tuple[SideEffectLevel, list[str]]:
    annotations = tool.annotations
    destructive_or_shell = capabilities & {
        Capability.DESTRUCTIVE_OPERATION,
        Capability.SHELL_EXECUTION,
    }

    if annotations and annotations.read_only_hint is True and not destructive_or_shell:
        return SideEffectLevel.NONE, ["annotated read-only with no conflicting signals"]

    if Capability.DESTRUCTIVE_OPERATION in capabilities:
        if capabilities & _HIGH_IMPACT_RESOURCES:
            return SideEffectLevel.CRITICAL, [
                "destructive operation on database, infrastructure, or filesystem resources"
            ]
        return SideEffectLevel.HIGH, ["destructive operation detected"]

    if Capability.SHELL_EXECUTION in capabilities:
        return SideEffectLevel.CRITICAL, ["executes arbitrary shell/system commands"]

    if Capability.NETWORK in capabilities and capabilities & _OUTBOUND_COMMUNICATION:
        return SideEffectLevel.HIGH, ["sends data over the network (e.g. notifications, messages)"]

    if Capability.DATA_WRITE in capabilities:
        return SideEffectLevel.MODERATE, ["creates or modifies data"]

    if Capability.READ_ONLY in capabilities:
        return SideEffectLevel.NONE, ["read-only signals with no write/destructive evidence"]

    return SideEffectLevel.LOW, ["no strong signals either way; treated as low-impact by default"]


def _recommendation_for(level: SideEffectLevel) -> str:
    if level in (SideEffectLevel.NONE, SideEffectLevel.LOW):
        return "No action needed."
    if level == SideEffectLevel.MODERATE:
        return "Ensure this tool's write operations are logged and reversible where possible."
    return "Require explicit confirmation or human approval before this tool is invoked."
