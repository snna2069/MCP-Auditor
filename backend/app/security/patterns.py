"""Deterministic regex heuristics for detecting adversarial tool-output
content, per SecurityTestCategory.

Like app.auditors.keywords, this is intentionally simple pattern matching
rather than an ML/LLM classifier: given the same input, results are always
identical, and patterns are reviewable in code rather than hidden in a
black-box model. False positives are expected and acceptable - the goal is
to surface suspicious content for human/agent-level review, not to make an
unappealable judgment.
"""

import re

from app.models.enums import SecurityTestCategory, Severity

_FLAGS = re.IGNORECASE | re.DOTALL


def _compile(*patterns: str) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(pattern, _FLAGS) for pattern in patterns)


CATEGORY_PATTERNS: dict[SecurityTestCategory, tuple[re.Pattern[str], ...]] = {
    SecurityTestCategory.PROMPT_INJECTION: _compile(
        r"ignore (all )?(the )?(above|previous) instructions",
        r"disregard (all )?(the )?(above|previous|prior) (instructions|rules|prompt)",
        r"new instructions?:",
        r"from now on,? you (are|must|should)",
    ),
    SecurityTestCategory.INSTRUCTION_OVERRIDE: _compile(
        r"override (your|the) (instructions|system prompt|rules)",
        r"forget (everything|all)( you (were|have been) told)?",
        r"your (new|real) (task|goal|instructions?) (is|are)",
        r"do not follow (your|the) (previous|original) instructions",
    ),
    SecurityTestCategory.DATA_EXFILTRATION_ATTEMPT: _compile(
        r"(send|email|post|upload|forward) (this|the|all) "
        r"(data|contents?|information|conversation) to",
        r"exfiltrat\w*",
    ),
    SecurityTestCategory.AUTHORITY_IMPERSONATION: _compile(
        r"as (the|your) (system administrator|developer|creator|owner)",
        r"this is an? (authorized|official) (override|instruction)",
        r"i am (the|your) (admin|administrator|developer|creator)",
        r"admin override",
    ),
    SecurityTestCategory.HIDDEN_INSTRUCTIONS: _compile(
        r"<!--.*?-->",
        r"note to (ai|assistant|model|llm)",
        r"\[(hidden|system)\]",
        r"[\u200b\u200c\u200d\ufeff]",
    ),
    SecurityTestCategory.TOOL_CONFUSION: _compile(
        r"now call (the )?(tool|function)",
        r"invoke (the )?(tool|function)\s+[\"']?\w+",
        r"</?tool_(result|call)>",
        r"system:\s*invoke",
    ),
}

# Severity assigned to a finding when this category's patterns match.
CATEGORY_SEVERITY: dict[SecurityTestCategory, Severity] = {
    SecurityTestCategory.PROMPT_INJECTION: Severity.HIGH,
    SecurityTestCategory.INSTRUCTION_OVERRIDE: Severity.CRITICAL,
    SecurityTestCategory.DATA_EXFILTRATION_ATTEMPT: Severity.CRITICAL,
    SecurityTestCategory.AUTHORITY_IMPERSONATION: Severity.HIGH,
    SecurityTestCategory.HIDDEN_INSTRUCTIONS: Severity.HIGH,
    SecurityTestCategory.TOOL_CONFUSION: Severity.MEDIUM,
}
