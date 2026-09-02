"""Audits tool descriptions for clarity and honest disclosure of risk."""

from app.auditors import keywords as kw
from app.auditors.base import BaseAuditor
from app.models.enums import AuditCategory, Severity
from app.schemas.audit_finding import AuditFinding
from app.schemas.tool_profile import ToolProfile

_MIN_DESCRIPTION_WORDS = 3

# Words that count as a description actually disclosing destructive/risky
# behavior, beyond just the same keyword used to detect the risk.
_DISCLOSURE_KEYWORDS = kw.DESTRUCTIVE_KEYWORDS | frozenset(
    {
        "permanent",
        "permanently",
        "irreversible",
        "irreversibly",
        "unrecoverable",
        "cannot be undone",
    }
)


class DescriptionAuditor(BaseAuditor):
    category = AuditCategory.TOOL_DEFINITION_QUALITY

    def audit(self, tool: ToolProfile) -> list[AuditFinding]:
        findings: list[AuditFinding] = []
        description = (tool.description or "").strip()

        if not description:
            findings.append(
                self._finding(
                    tool,
                    severity=Severity.MEDIUM,
                    title="Tool has no description",
                    description=(
                        f"Tool '{tool.name}' does not provide a description, so its "
                        "behavior cannot be assessed from metadata alone."
                    ),
                    recommendation=(
                        "Add a clear description of what this tool does, including "
                        "any side effects."
                    ),
                )
            )
        elif len(description.split()) < _MIN_DESCRIPTION_WORDS:
            findings.append(
                self._finding(
                    tool,
                    severity=Severity.LOW,
                    title="Tool description is too brief",
                    description=(
                        f"Tool '{tool.name}' has a description of only "
                        f"{len(description.split())} word(s), which is unlikely to "
                        "convey its behavior clearly."
                    ),
                    recommendation=(
                        "Expand the description to explain what the tool does and any side effects."
                    ),
                    evidence={"description": description},
                )
            )

        findings.extend(self._check_destructive_disclosure(tool, description))
        return findings

    def _check_destructive_disclosure(
        self, tool: ToolProfile, description: str
    ) -> list[AuditFinding]:
        name_signals = kw.find_matches(kw.normalize(tool.name), kw.DESTRUCTIVE_KEYWORDS)
        annotation_signal = bool(tool.annotations and tool.annotations.destructive_hint is True)

        if not name_signals and not annotation_signal:
            return []

        disclosed = bool(kw.find_matches(kw.normalize(description), _DISCLOSURE_KEYWORDS))
        if disclosed:
            return []

        reasons = []
        if name_signals:
            reasons.append(f"name suggests a destructive action ({', '.join(name_signals)})")
        if annotation_signal:
            reasons.append("server-reported annotations mark this tool as destructive")

        return [
            self._finding(
                tool,
                severity=Severity.HIGH,
                title="Tool description does not disclose destructive behavior",
                description=(
                    f"Tool '{tool.name}' appears destructive ({'; '.join(reasons)}), "
                    "but its description does not mention this. Callers may invoke "
                    "it without realizing it causes irreversible changes."
                ),
                recommendation=(
                    "Update the description to clearly state that this tool performs "
                    "a destructive, irreversible action."
                ),
                evidence={
                    "name_signals": name_signals,
                    "annotation_destructive_hint": annotation_signal,
                    "description": description,
                },
            )
        ]
