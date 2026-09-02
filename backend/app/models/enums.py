"""Domain enums shared by ORM models and Pydantic schemas."""

import enum


class SourceType(enum.StrEnum):
    """How an MCP server is connected to / located."""

    LOCAL_COMMAND = "LOCAL_COMMAND"
    HTTP = "HTTP"
    SSE = "SSE"
    PACKAGE = "PACKAGE"
    MANUAL_CONFIGURATION = "MANUAL_CONFIGURATION"


# Source types the ingestion API accepts as of Phase 1. SSE and PACKAGE are
# part of the long-term domain model but are not implemented yet.
SUPPORTED_SOURCE_TYPES: frozenset[SourceType] = frozenset(
    {
        SourceType.LOCAL_COMMAND,
        SourceType.HTTP,
        SourceType.MANUAL_CONFIGURATION,
    }
)


class DiscoveryStatus(enum.StrEnum):
    """Outcome of the most recent tool-discovery attempt for a server."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Severity(enum.StrEnum):
    """Severity of a single AuditFinding."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AuditCategory(enum.StrEnum):
    """Which audit dimension a finding belongs to.

    Mirrors the five audit dimensions in PROJECT_PLAN.md. Not every category
    has an auditor yet (PROMPT_INJECTION_RISK is Phase 6;
    HALLUCINATION_RELIABILITY_RISK has no dedicated auditor yet) - the enum
    is defined up front since it's a stable taxonomy, and the scoring engine
    (Phase 4) will need it regardless of which categories currently produce
    findings.
    """

    TOOL_DEFINITION_QUALITY = "TOOL_DEFINITION_QUALITY"
    CAPABILITY_PERMISSION_RISK = "CAPABILITY_PERMISSION_RISK"
    PROMPT_INJECTION_RISK = "PROMPT_INJECTION_RISK"
    HALLUCINATION_RELIABILITY_RISK = "HALLUCINATION_RELIABILITY_RISK"
    SIDE_EFFECT_ANALYSIS = "SIDE_EFFECT_ANALYSIS"


class Capability(enum.StrEnum):
    """Normalized capability tags a tool may be inferred to have."""

    READ_ONLY = "READ_ONLY"
    DATA_WRITE = "DATA_WRITE"
    FILE_SYSTEM = "FILE_SYSTEM"
    NETWORK = "NETWORK"
    SHELL_EXECUTION = "SHELL_EXECUTION"
    DATABASE = "DATABASE"
    SECRETS_ACCESS = "SECRETS_ACCESS"
    IDENTITY_ACCESS = "IDENTITY_ACCESS"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    DESTRUCTIVE_OPERATION = "DESTRUCTIVE_OPERATION"


class SideEffectLevel(enum.StrEnum):
    """How impactful invoking a tool is expected to be."""

    NONE = "NONE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskLevel(enum.StrEnum):
    """Overall risk classification derived from a numerical score.

    Thresholds are configurable (see app.scoring.config.ScoringConfig) - this
    enum only defines the fixed set of classification labels.
    """

    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AuditStatus(enum.StrEnum):
    """Lifecycle state of a single Audit execution."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SecurityTestCategory(enum.StrEnum):
    """Categories of adversarial tool-output content (Phase 6).

    Findings produced by the detector that uses these are recorded under
    AuditCategory.PROMPT_INJECTION_RISK; this enum is a finer-grained
    breakdown of *which kind* of prompt-injection-style content was found.
    """

    PROMPT_INJECTION = "PROMPT_INJECTION"
    INSTRUCTION_OVERRIDE = "INSTRUCTION_OVERRIDE"
    DATA_EXFILTRATION_ATTEMPT = "DATA_EXFILTRATION_ATTEMPT"
    AUTHORITY_IMPERSONATION = "AUTHORITY_IMPERSONATION"
    HIDDEN_INSTRUCTIONS = "HIDDEN_INSTRUCTIONS"
    TOOL_CONFUSION = "TOOL_CONFUSION"
