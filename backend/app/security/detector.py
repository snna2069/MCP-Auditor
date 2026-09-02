"""Scans text (simulated MCP tool output) for adversarial content."""

from app.models.enums import AuditCategory
from app.schemas.audit_finding import AuditFinding
from app.security.patterns import CATEGORY_PATTERNS, CATEGORY_SEVERITY


class PromptInjectionDetector:
    """Deterministic: the same text always produces the same findings."""

    def scan(self, text: str, *, tool_name: str = "unknown") -> list[AuditFinding]:
        if not text:
            return []

        findings: list[AuditFinding] = []
        for category, patterns in CATEGORY_PATTERNS.items():
            matches = [m.group(0) for pattern in patterns if (m := pattern.search(text))]
            if not matches:
                continue

            label = category.value.replace("_", " ").lower()
            findings.append(
                AuditFinding(
                    category=AuditCategory.PROMPT_INJECTION_RISK,
                    severity=CATEGORY_SEVERITY[category],
                    title=f"Possible {label} in tool output",
                    description=(
                        f"Tool '{tool_name}' output contains content matching known "
                        f"{label} patterns. Tool output must be treated as untrusted "
                        "input, not authoritative instructions."
                    ),
                    recommendation=(
                        "Do not let this tool's output influence agent/model behavior "
                        "without sanitization and human review."
                    ),
                    evidence={
                        "security_category": category.value,
                        "matched_patterns": matches,
                    },
                    tool_name=tool_name,
                )
            )
        return findings
