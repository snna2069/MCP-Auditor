"""Render the canonical audit report as a paginated PDF."""

import json
from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.report import AuditReport, ReportFinding


def render_audit_report_pdf(report: AuditReport) -> bytes:
    """Render all canonical report fields into a downloadable PDF."""
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title="MCP audit report",
        author="MCP Server Auditor",
    )
    styles = getSampleStyleSheet()
    styles.add(styles["Title"].clone("ReportTitle", alignment=TA_CENTER, fontSize=20))
    styles.add(styles["Heading2"].clone("ReportHeading", spaceBefore=12, spaceAfter=6))
    styles.add(styles["Heading3"].clone("FindingHeading", spaceBefore=10, spaceAfter=4))
    styles.add(styles["BodyText"].clone("ReportBody", leading=14, spaceAfter=4))
    styles.add(styles["Code"].clone("Evidence", fontName="Courier", fontSize=7.5, leading=9))
    styles.add(styles["BodyText"].clone("Muted", textColor=colors.HexColor("#5d6875")))

    story = [
        Paragraph("MCP audit report", styles["ReportTitle"]),
        Paragraph(
            f"Report schema {_paragraph_text(report.report_metadata.schema_version)} | "
            f"{_paragraph_text(report.report_metadata.report_timestamp)}",
            styles["Muted"],
        ),
        Spacer(1, 10),
        Paragraph("Server and audit", styles["ReportHeading"]),
        _metadata_table(report, styles),
        Paragraph("Risk summary", styles["ReportHeading"]),
        _metadata_table(
            report,
            styles,
            rows=[
                ("Overall score", report.overall_score),
                ("Risk level", report.risk_level),
            ],
        ),
        Paragraph("Category breakdown", styles["ReportHeading"]),
        _key_value_table(
            ((category.value, score) for category, score in report.category_scores.items()),
            styles,
            "No category scores.",
        ),
        Paragraph("Severity breakdown", styles["ReportHeading"]),
        _key_value_table(
            ((severity.value, count) for severity, count in report.severity_breakdown.items()),
            styles,
            "No severity data.",
        ),
        Paragraph("Score contributors", styles["ReportHeading"]),
        _contributors_table(report, styles),
        Paragraph("Findings", styles["ReportHeading"]),
    ]
    story.extend(_finding_flowables(report.findings, styles))
    document.build(story)
    return buffer.getvalue()


def _metadata_table(
    report: AuditReport,
    styles: dict[str, Any],
    rows: list[tuple[str, Any]] | None = None,
) -> Table:
    if rows is None:
        rows = [
            ("MCP server", report.server.name),
            ("Server ID", report.server.id),
            ("Source type", report.server.source_type),
            ("Discovery status", report.server.last_discovery_status or "Not available"),
            ("Audit ID", report.audit_id),
            ("Audit version", report.audit_version),
            ("Created", report.created_at),
            ("Started", report.started_at or "Not available"),
            ("Completed", report.completed_at),
            ("Date/time", report.report_metadata.report_timestamp),
        ]
    return _key_value_table(rows, styles, "No metadata.")


def _key_value_table(
    rows: Any,
    styles: dict[str, Any],
    empty_message: str,
) -> Table:
    items = list(rows)
    data = [[Paragraph("Field", styles["Muted"]), Paragraph("Value", styles["Muted"])]]
    if items:
        data.extend(
            [
                [
                    Paragraph(_paragraph_text(name), styles["ReportBody"]),
                    Paragraph(_paragraph_text(value), styles["ReportBody"]),
                ]
                for name, value in items
            ]
        )
    else:
        data.append([Paragraph(_paragraph_text(empty_message), styles["ReportBody"]), ""])
    return _styled_table(data)


def _contributors_table(report: AuditReport, styles: dict[str, Any]) -> Table:
    data = [
        [
            Paragraph("Tool", styles["Muted"]),
            Paragraph("Finding", styles["Muted"]),
            Paragraph("Severity", styles["Muted"]),
            Paragraph("Contribution", styles["Muted"]),
        ]
    ]
    data.extend(
        [
            Paragraph(_paragraph_text(contributor.tool_name), styles["ReportBody"]),
            Paragraph(_paragraph_text(contributor.title), styles["ReportBody"]),
            Paragraph(_paragraph_text(contributor.severity), styles["ReportBody"]),
            Paragraph(_paragraph_text(contributor.contribution), styles["ReportBody"]),
        ]
        for contributor in report.score_contributors
    )
    if len(data) == 1:
        data.append([Paragraph("No score contributors.", styles["ReportBody"]), "", "", ""])
    return _styled_table(data, widths=[1.3 * inch, 2.9 * inch, 1.0 * inch, 1.0 * inch])


def _finding_flowables(findings: list[ReportFinding], styles: dict[str, Any]) -> list[Any]:
    if not findings:
        return [Paragraph("No findings.", styles["Muted"])]

    flowables: list[Any] = []
    for finding in findings:
        flowables.extend(
            [
                Paragraph(_paragraph_text(finding.title), styles["FindingHeading"]),
                _key_value_table(
                    [
                        ("Finding ID", finding.id),
                        ("Category", finding.category),
                        ("Severity", finding.severity),
                        ("Tool", finding.tool_name),
                    ],
                    styles,
                    "No finding details.",
                ),
                Paragraph("Description", styles["FindingHeading"]),
                Paragraph(_paragraph_text(finding.description), styles["ReportBody"]),
                Paragraph("Recommendation", styles["FindingHeading"]),
                Paragraph(_paragraph_text(finding.recommendation), styles["ReportBody"]),
                Paragraph("Evidence", styles["FindingHeading"]),
                Paragraph(_paragraph_text(_evidence_text(finding.evidence)), styles["Evidence"]),
                Spacer(1, 8),
            ]
        )
    return flowables


def _evidence_text(evidence: dict[str, Any]) -> str:
    return json.dumps(evidence, indent=2, sort_keys=True, default=str)


def _paragraph_text(value: Any) -> str:
    return escape(str(value)).replace("\n", "<br/>")


def _styled_table(data: list[list[Any]], widths: list[float] | None = None) -> Table:
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d9dee5")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f4f6f8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table
