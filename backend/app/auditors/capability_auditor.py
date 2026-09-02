"""Audits a tool's inferred capabilities for high-risk signals."""

from app.auditors.base import BaseAuditor
from app.auditors.capability_inference import CapabilityEvidence, infer_capabilities
from app.models.enums import AuditCategory, Capability, Severity
from app.schemas.audit_finding import AuditFinding
from app.schemas.tool_profile import ToolProfile

# Combinations of capabilities that are especially dangerous together.
_DANGEROUS_COMBINATIONS: list[tuple[frozenset[Capability], Severity, str]] = [
    (
        frozenset({Capability.SHELL_EXECUTION, Capability.NETWORK}),
        Severity.CRITICAL,
        "combines shell execution and network access",
    ),
    (
        frozenset({Capability.SHELL_EXECUTION, Capability.DESTRUCTIVE_OPERATION}),
        Severity.CRITICAL,
        "combines shell execution and destructive operations",
    ),
    (
        frozenset({Capability.DESTRUCTIVE_OPERATION, Capability.INFRASTRUCTURE}),
        Severity.HIGH,
        "can destructively modify infrastructure",
    ),
    (
        frozenset({Capability.SECRETS_ACCESS, Capability.NETWORK}),
        Severity.HIGH,
        "can access secrets and has network access (possible exfiltration risk)",
    ),
]

_MISMATCH_CAPABILITIES = frozenset({Capability.DESTRUCTIVE_OPERATION, Capability.SHELL_EXECUTION})


class CapabilityAuditor(BaseAuditor):
    category = AuditCategory.CAPABILITY_PERMISSION_RISK

    def audit(self, tool: ToolProfile) -> list[AuditFinding]:
        capabilities, evidence = infer_capabilities(tool)
        findings: list[AuditFinding] = []

        findings.extend(self._check_unrestricted_command_input(tool, capabilities))
        findings.extend(self._check_dangerous_combinations(tool, capabilities, evidence))
        findings.extend(self._check_annotation_mismatch(tool, capabilities, evidence))

        if not findings and capabilities <= {Capability.READ_ONLY}:
            findings.append(
                self._finding(
                    tool,
                    severity=Severity.INFO,
                    title="No elevated capabilities detected",
                    description=(f"Tool '{tool.name}' shows no signals of elevated capabilities."),
                    recommendation="No action needed.",
                    evidence={"capabilities": sorted(c.value for c in capabilities)},
                )
            )

        return findings

    def _check_unrestricted_command_input(
        self, tool: ToolProfile, capabilities: set[Capability]
    ) -> list[AuditFinding]:
        if Capability.SHELL_EXECUTION not in capabilities:
            return []

        unconstrained = _unconstrained_string_params(tool)
        if not unconstrained:
            return []

        return [
            self._finding(
                tool,
                severity=Severity.CRITICAL,
                title="Tool accepts unrestricted command input",
                description=(
                    f"Tool '{tool.name}' appears to execute shell/system commands and "
                    f"accepts free-form string parameter(s) ({', '.join(unconstrained)}) "
                    "with no schema constraints (no enum, pattern, or length limit)."
                ),
                recommendation=(
                    "Constrain command-like parameters with an enum, pattern, or "
                    "allow-list, or require structured arguments instead of raw strings."
                ),
                evidence={"unconstrained_parameters": unconstrained},
            )
        ]

    def _check_dangerous_combinations(
        self,
        tool: ToolProfile,
        capabilities: set[Capability],
        evidence: CapabilityEvidence,
    ) -> list[AuditFinding]:
        findings = []
        for combo, severity, description in _DANGEROUS_COMBINATIONS:
            if not combo <= capabilities:
                continue
            findings.append(
                self._finding(
                    tool,
                    severity=severity,
                    title="Tool combines multiple high-risk capabilities",
                    description=f"Tool '{tool.name}' {description}.",
                    recommendation=(
                        "Split this tool's responsibilities, or require explicit "
                        "human approval before invocation."
                    ),
                    evidence={
                        "capabilities": sorted(c.value for c in combo),
                        "keyword_evidence": {c.value: evidence.get(c, []) for c in combo},
                    },
                )
            )
        return findings

    def _check_annotation_mismatch(
        self,
        tool: ToolProfile,
        capabilities: set[Capability],
        evidence: CapabilityEvidence,
    ) -> list[AuditFinding]:
        annotations = tool.annotations
        if not annotations or annotations.read_only_hint is not True:
            return []

        risky = capabilities & _MISMATCH_CAPABILITIES
        if not risky:
            return []

        return [
            self._finding(
                tool,
                severity=Severity.CRITICAL,
                title="Tool annotations claim read-only but appear destructive",
                description=(
                    f"Tool '{tool.name}' is annotated readOnlyHint=true, but keyword "
                    f"analysis suggests it may perform "
                    f"{', '.join(sorted(c.value for c in risky))} actions. "
                    "Server-reported annotations are untrusted and may be misleading."
                ),
                recommendation=(
                    "Do not rely on this tool's annotations alone; verify its actual "
                    "behavior before granting it read-only trust."
                ),
                evidence={
                    "read_only_hint": True,
                    "conflicting_capabilities": sorted(c.value for c in risky),
                    "keyword_evidence": {c.value: evidence.get(c, []) for c in risky},
                },
            )
        ]


def _unconstrained_string_params(tool: ToolProfile) -> list[str]:
    schema = tool.input_schema or {}
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return []

    unconstrained = []
    for name, prop in properties.items():
        if not isinstance(prop, dict) or prop.get("type") != "string":
            continue
        if any(key in prop for key in ("enum", "pattern", "maxLength", "format")):
            continue
        unconstrained.append(name)
    return sorted(unconstrained)
