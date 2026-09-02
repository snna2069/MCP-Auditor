"""Model Context Protocol client implementations.

This package is intentionally isolated from the auditing engine (see
app.auditors, added in Phase 3) so that protocol-specific behavior can
evolve independently. Nothing here should contain audit/scoring logic.
"""
