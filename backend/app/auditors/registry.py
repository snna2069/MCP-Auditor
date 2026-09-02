"""Registry of the default auditors and a convenience runner.

Used by tests to demonstrate deterministic findings, and will be reused by
the Phase 5 audit execution pipeline to run every auditor against every
discovered tool.
"""

from app.auditors.base import BaseAuditor
from app.auditors.capability_auditor import CapabilityAuditor
from app.auditors.description_auditor import DescriptionAuditor
from app.auditors.schema_auditor import SchemaAuditor
from app.auditors.side_effect_auditor import SideEffectAuditor
from app.schemas.audit_finding import AuditFinding
from app.schemas.tool_profile import ToolProfile

# Recorded on each Audit (Audit.audit_version) so results can be tied back
# to the auditor/scoring logic version that produced them. Bump when
# auditor behavior changes in a way that could change findings.
AUDITOR_ENGINE_VERSION = "1.0.0"

DEFAULT_AUDITORS: tuple[BaseAuditor, ...] = (
    DescriptionAuditor(),
    SchemaAuditor(),
    CapabilityAuditor(),
    SideEffectAuditor(),
)


def run_auditors(
    tool: ToolProfile, auditors: tuple[BaseAuditor, ...] = DEFAULT_AUDITORS
) -> list[AuditFinding]:
    """Run every auditor against ``tool`` and return all findings."""
    findings: list[AuditFinding] = []
    for auditor in auditors:
        findings.extend(auditor.audit(tool))
    return findings
