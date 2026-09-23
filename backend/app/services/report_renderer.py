"""Render canonical audit reports as escaped, self-contained HTML."""

import html
import json
import logging
import time
from collections.abc import Iterable
from typing import Any

from app.core.observability import correlation_fields, elapsed, metrics
from app.schemas.report import AuditReport, ReportFinding

logger = logging.getLogger(__name__)


def render_audit_report_html(report: AuditReport) -> str:
    """Render every report field from the canonical ``AuditReport`` model."""
    started = time.monotonic()
    categories = _render_rows(
        ((category.value, score) for category, score in report.category_scores.items()),
        empty_message="No category scores.",
    )
    severities = _render_rows(
        ((severity.value, count) for severity, count in report.severity_breakdown.items()),
        empty_message="No severity data.",
    )
    contributors = _render_contributors(report.score_contributors)
    findings = _render_findings(report.findings)

    rendered = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Audit report - {_text(report.server.name)}</title>
  <style>
    :root {{ color-scheme: light; font-family: system-ui, sans-serif; }}
    body {{ margin: 0; color: #17202a; background: #f4f6f8; }}
    main {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 56px; }}
    section {{ margin-top: 24px; padding: 20px; background: #fff; border: 1px solid #d9dee5;
      border-radius: 8px; }}
    h1, h2, h3 {{ margin-top: 0; }}
    h1 {{ font-size: 28px; }}
    h2 {{ font-size: 20px; }}
    h3 {{ margin-bottom: 8px; font-size: 16px; }}
    dl {{ display: grid; grid-template-columns: minmax(140px, 220px) 1fr; gap: 8px 16px; }}
    dt {{ color: #5d6875; font-weight: 600; }}
    dd {{ margin: 0; overflow-wrap: anywhere; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 10px 8px; text-align: left; vertical-align: top;
      border-bottom: 1px solid #e5e8eb; }}
    th {{ color: #5d6875; font-size: 13px; }}
    pre {{ margin: 8px 0 0; padding: 12px; overflow-x: auto; background: #f4f6f8;
      border-radius: 6px; white-space: pre-wrap; }}
    .score {{ font-size: 32px; font-weight: 700; }}
    .muted {{ color: #5d6875; }}
    .finding {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e8eb; }}
    .finding:first-child {{ margin-top: 0; padding-top: 0; border-top: 0; }}
  </style>
</head>
<body>
  <main>
    <h1>MCP audit report</h1>
    <p class="muted">Report schema {_text(report.report_metadata.schema_version)} ·
      {_text(report.report_metadata.report_timestamp)}</p>

    <section>
      <h2>Server and audit</h2>
      <dl>
        <dt>Server</dt><dd>{_text(report.server.name)}</dd>
        <dt>Server ID</dt><dd>{_text(report.server.id)}</dd>
        <dt>Source type</dt><dd>{_text(report.server.source_type)}</dd>
        <dt>Discovery status</dt><dd>{
        _text(report.server.last_discovery_status or "Not available")
    }</dd>
        <dt>Audit ID</dt><dd>{_text(report.audit_id)}</dd>
        <dt>Audit version</dt><dd>{_text(report.audit_version)}</dd>
        <dt>Created</dt><dd>{_text(report.created_at)}</dd>
        <dt>Started</dt><dd>{_text(report.started_at or "Not available")}</dd>
        <dt>Completed</dt><dd>{_text(report.completed_at)}</dd>
        <dt>Audit timestamp</dt><dd>{_text(report.report_metadata.report_timestamp)}</dd>
      </dl>
    </section>

    <section>
      <h2>Risk summary</h2>
      <p class="score">{_text(report.overall_score)} <span class="muted">/ 100</span></p>
      <p>Risk level: <strong>{_text(report.risk_level)}</strong></p>
    </section>

    <section>
      <h2>Category breakdown</h2>
      {categories}
    </section>

    <section>
      <h2>Severity breakdown</h2>
      {severities}
    </section>

    <section>
      <h2>Score contributors</h2>
      {contributors}
    </section>

    <section>
      <h2>Findings</h2>
      {findings}
    </section>
  </main>
</body>
</html>
"""
    metrics.observe("report_render_duration_seconds", elapsed(started), format="html")
    logger.info(
        "report rendered",
        extra=correlation_fields(
            audit_id=report.audit_id, format="html", duration_seconds=elapsed(started)
        ),
    )
    return rendered


def _text(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _json(value: Any) -> str:
    serialized = json.dumps(value, indent=2, sort_keys=True, default=str)
    return _text(serialized)


def _render_rows(rows: Iterable[tuple[Any, Any]], *, empty_message: str) -> str:
    items = list(rows)
    if not items:
        return f'<p class="muted">{_text(empty_message)}</p>'
    return (
        "<table><thead><tr><th>Name</th><th>Value</th></tr></thead><tbody>"
        + "".join(
            f"<tr><td>{_text(name)}</td><td>{_text(value)}</td></tr>" for name, value in items
        )
        + "</tbody></table>"
    )


def _render_contributors(contributors: list[Any]) -> str:
    if not contributors:
        return '<p class="muted">No score contributors.</p>'
    return (
        "<table><thead><tr><th>Tool</th><th>Finding</th><th>Severity</th>"
        "<th>Contribution</th></tr></thead><tbody>"
        + "".join(
            "<tr>"
            f"<td>{_text(contributor.tool_name)}</td>"
            f"<td>{_text(contributor.title)}</td>"
            f"<td>{_text(contributor.severity)}</td>"
            f"<td>{_text(contributor.contribution)}</td>"
            "</tr>"
            for contributor in contributors
        )
        + "</tbody></table>"
    )


def _render_findings(findings: list[ReportFinding]) -> str:
    if not findings:
        return '<p class="muted">No findings.</p>'
    return "".join(
        f"""<article class="finding">
  <h3>{_text(finding.title)}</h3>
  <dl>
    <dt>Finding ID</dt><dd>{_text(finding.id)}</dd>
    <dt>Category</dt><dd>{_text(finding.category)}</dd>
    <dt>Severity</dt><dd>{_text(finding.severity)}</dd>
    <dt>Tool</dt><dd>{_text(finding.tool_name)}</dd>
    <dt>Description</dt><dd>{_text(finding.description)}</dd>
    <dt>Recommendation</dt><dd>{_text(finding.recommendation)}</dd>
  </dl>
  <h3>Evidence</h3>
  <pre>{_json(finding.evidence)}</pre>
</article>"""
        for finding in findings
    )
