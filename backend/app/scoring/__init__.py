"""Risk scoring engine (Phase 4).

Converts a list of AuditFinding into an explainable numerical score and
risk classification. See app.scoring.config.ScoringConfig for the single
place all scoring numbers (baseline, weights, thresholds) live - nothing
here or in the auditors should hardcode a risk score.
"""
