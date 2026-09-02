"""Deterministic audit engine (Phase 3).

Each auditor accepts a ToolProfile and returns a list of AuditFinding
objects. Auditors must be pure/deterministic: given the same ToolProfile,
they always produce the same findings (no randomness, no network or model
calls) so audits are reproducible.
"""
