"""Security test harness (Phase 6): a reusable adversarial payload library
and a deterministic detector for prompt-injection-style content in
(simulated) MCP tool output.

Per the project's security principles, nothing in this package executes a
real MCP tool. It only scans text handed to it - from curated fixtures
here, or later from tool-call output captured by an explicitly-authorized,
separate invocation step (not built yet; Phase 6 does not add tool
execution).
"""
