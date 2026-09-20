"""API tests for stable JSON audit reports."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit import Audit
from app.models.audit_finding import AuditFinding
from app.models.enums import AuditCategory, AuditStatus, RiskLevel, Severity, SourceType
from app.models.mcp_server import MCPServer
from app.schemas.mcp_server import MCPServerCreate
from app.services.mcp_server_service import MCPServerService


def _create_server(db_session: Session, *, name: str = "report-server") -> MCPServer:
    server = MCPServerService(db_session).create_server(
        MCPServerCreate(
            name=name,
            source_type=SourceType.MANUAL_CONFIGURATION,
            connection_config={"details": {"tools": []}},
        )
    )
    return server


def _create_audit(
    db_session: Session,
    server: MCPServer,
    *,
    status: AuditStatus = AuditStatus.COMPLETED,
    findings: list[dict] | None = None,
) -> Audit:
    audit = Audit(
        server_id=server.id,
        status=status,
        audit_version="test-engine",
        overall_score=100.0 if status == AuditStatus.COMPLETED else None,
        risk_level=RiskLevel.LOW if status == AuditStatus.COMPLETED else None,
    )
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)

    for finding in findings or []:
        db_session.add(AuditFinding(audit_id=audit.id, **finding))
    db_session.commit()
    return audit


def test_report_generation_includes_stable_audit_data(
    client: TestClient, db_session: Session
) -> None:
    server = _create_server(db_session)
    audit = _create_audit(db_session, server)

    response = client.get(f"/audits/{audit.id}/report")

    assert response.status_code == 200
    body = response.json()
    assert body["report_metadata"]["schema_version"] == "1"
    assert body["server"]["name"] == "report-server"
    assert body["audit_id"] == str(audit.id)
    assert body["audit_version"] == "test-engine"
    assert body["overall_score"] == 100.0
    assert body["risk_level"] == "LOW"
    assert body["findings"] == []


def test_report_for_missing_audit_returns_404(client: TestClient) -> None:
    response = client.get(f"/audits/{uuid.uuid4()}/report")

    assert response.status_code == 404


def test_report_for_incomplete_audit_returns_409(client: TestClient, db_session: Session) -> None:
    server = _create_server(db_session)
    audit = _create_audit(db_session, server, status=AuditStatus.RUNNING)

    response = client.get(f"/audits/{audit.id}/report")

    assert response.status_code == 409


def test_report_for_zero_findings_has_zero_severity_counts(
    client: TestClient, db_session: Session
) -> None:
    server = _create_server(db_session)
    audit = _create_audit(db_session, server)

    body = client.get(f"/audits/{audit.id}/report").json()

    assert body["findings"] == []
    assert body["severity_breakdown"] == {severity.value: 0 for severity in Severity}


def test_report_includes_multiple_severities(client: TestClient, db_session: Session) -> None:
    server = _create_server(db_session)
    audit = _create_audit(
        db_session,
        server,
        findings=[
            {
                "category": AuditCategory.TOOL_DEFINITION_QUALITY,
                "severity": Severity.HIGH,
                "title": "High finding",
                "description": "High description",
                "evidence": {"source": "fixture"},
                "recommendation": "Review it",
                "tool_name": "dangerous_tool",
            },
            {
                "category": AuditCategory.SIDE_EFFECT_ANALYSIS,
                "severity": Severity.LOW,
                "title": "Low finding",
                "description": "Low description",
                "evidence": {"source": "fixture"},
                "recommendation": "Monitor it",
                "tool_name": "mild_tool",
            },
        ],
    )

    body = client.get(f"/audits/{audit.id}/report").json()

    assert body["severity_breakdown"]["HIGH"] == 1
    assert body["severity_breakdown"]["LOW"] == 1
    assert len(body["findings"]) == 2
    assert body["findings"][0]["evidence"] == {"source": "fixture"}


def test_report_does_not_expose_sensitive_server_configuration(
    client: TestClient, db_session: Session
) -> None:
    server_response = client.post(
        "/servers",
        json={
            "name": "secret-report-server",
            "source_type": "HTTP",
            "connection_config": {
                "url": "https://example.test/mcp",
                "headers": {"Authorization": "Bearer super-secret-token"},
            },
        },
    )
    server = db_session.get(MCPServer, uuid.UUID(server_response.json()["id"]))
    assert server is not None
    audit = _create_audit(db_session, server)

    report_text = client.get(f"/audits/{audit.id}/report").text

    assert "super-secret-token" not in report_text
    assert "Authorization" not in report_text
    assert "connection_config" not in report_text


def test_html_report_generation_has_correct_content_type_and_sections(
    client: TestClient, db_session: Session
) -> None:
    server = _create_server(db_session)
    audit = _create_audit(db_session, server)

    response = client.get(f"/audits/{audit.id}/report/html")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "MCP audit report" in response.text
    assert "Server and audit" in response.text
    assert "Risk summary" in response.text
    assert "Category breakdown" in response.text
    assert "Severity breakdown" in response.text
    assert "Findings" in response.text
    assert "No findings." in response.text


def test_html_report_for_missing_audit_returns_404(client: TestClient) -> None:
    response = client.get(f"/audits/{uuid.uuid4()}/report/html")

    assert response.status_code == 404


def test_html_report_escapes_untrusted_finding_content(
    client: TestClient, db_session: Session
) -> None:
    server = _create_server(db_session)
    audit = _create_audit(
        db_session,
        server,
        findings=[
            {
                "category": AuditCategory.TOOL_DEFINITION_QUALITY,
                "severity": Severity.HIGH,
                "title": '<script>alert("xss")</script>',
                "description": "Description with <b>markup</b> & characters",
                "evidence": {"payload": '<img src=x onerror="alert(1)">'},
                "recommendation": "Use a <safe> description",
                "tool_name": "tool<&",
            }
        ],
    )

    response = client.get(f"/audits/{audit.id}/report/html")

    assert response.status_code == 200
    assert '<script>alert("xss")</script>' not in response.text
    assert "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;" in response.text
    assert "&lt;img src=x onerror=\\&quot;alert(1)\\&quot;&gt;" in response.text
    assert "<b>markup</b>" not in response.text


def test_html_report_does_not_expose_sensitive_server_configuration(
    client: TestClient, db_session: Session
) -> None:
    server_response = client.post(
        "/servers",
        json={
            "name": "secret-html-report-server",
            "source_type": "HTTP",
            "connection_config": {
                "url": "https://example.test/mcp",
                "headers": {"Authorization": "Bearer html-secret-token"},
            },
        },
    )
    server = db_session.get(MCPServer, uuid.UUID(server_response.json()["id"]))
    assert server is not None
    audit = _create_audit(db_session, server)

    report_text = client.get(f"/audits/{audit.id}/report/html").text

    assert "html-secret-token" not in report_text
    assert "Authorization" not in report_text
    assert "connection_config" not in report_text


def test_html_report_renders_multiple_findings(client: TestClient, db_session: Session) -> None:
    server = _create_server(db_session)
    audit = _create_audit(
        db_session,
        server,
        findings=[
            {
                "category": AuditCategory.TOOL_DEFINITION_QUALITY,
                "severity": Severity.HIGH,
                "title": "High finding",
                "description": "High description",
                "evidence": {"source": "high"},
                "recommendation": "Review high finding",
                "tool_name": "dangerous_tool",
            },
            {
                "category": AuditCategory.SIDE_EFFECT_ANALYSIS,
                "severity": Severity.LOW,
                "title": "Low finding",
                "description": "Low description",
                "evidence": {"source": "low"},
                "recommendation": "Review low finding",
                "tool_name": "mild_tool",
            },
        ],
    )

    report_text = client.get(f"/audits/{audit.id}/report/html").text

    assert "High finding" in report_text
    assert "Low finding" in report_text
    assert "Review high finding" in report_text
    assert "Review low finding" in report_text
    assert "&quot;source&quot;: &quot;high&quot;" in report_text
    assert "&quot;source&quot;: &quot;low&quot;" in report_text


def test_pdf_report_generation_returns_downloadable_pdf(
    client: TestClient, db_session: Session
) -> None:
    server = _create_server(db_session)
    audit = _create_audit(db_session, server)

    response = client.get(f"/audits/{audit.id}/report/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == (
        f'attachment; filename="audit-{audit.id}.pdf"'
    )
    assert response.content.startswith(b"%PDF-")
    assert len(response.content) > 1_000


def test_pdf_report_for_missing_audit_returns_404(client: TestClient) -> None:
    response = client.get(f"/audits/{uuid.uuid4()}/report/pdf")

    assert response.status_code == 404


def test_pdf_report_with_empty_findings_is_valid(client: TestClient, db_session: Session) -> None:
    server = _create_server(db_session)
    audit = _create_audit(db_session, server)

    response = client.get(f"/audits/{audit.id}/report/pdf")

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")


def test_pdf_report_handles_large_findings(client: TestClient, db_session: Session) -> None:
    server = _create_server(db_session)
    long_text = "Large finding content. " * 500
    audit = _create_audit(
        db_session,
        server,
        findings=[
            {
                "category": AuditCategory.TOOL_DEFINITION_QUALITY,
                "severity": Severity.HIGH,
                "title": f"Large finding {index}",
                "description": long_text,
                "evidence": {"payload": long_text},
                "recommendation": long_text,
                "tool_name": f"large_tool_{index}",
            }
            for index in range(12)
        ],
    )

    response = client.get(f"/audits/{audit.id}/report/pdf")

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")
    assert len(response.content) > 10_000


def test_pdf_report_handles_special_characters(client: TestClient, db_session: Session) -> None:
    server = _create_server(db_session)
    audit = _create_audit(
        db_session,
        server,
        findings=[
            {
                "category": AuditCategory.PROMPT_INJECTION_RISK,
                "severity": Severity.CRITICAL,
                "title": '<script>alert("xss")</script> & finding',
                "description": "Text with <tags>, ampersands, and quotes: ' \"",
                "evidence": {"payload": '<img src=x onerror="alert(1)">'},
                "recommendation": "Escape <all> untrusted content & keep it inert",
                "tool_name": "tool<&",
            }
        ],
    )

    response = client.get(f"/audits/{audit.id}/report/pdf")

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")
    assert b"<script>alert" not in response.content


def test_pdf_report_does_not_expose_sensitive_server_configuration(
    client: TestClient, db_session: Session
) -> None:
    server_response = client.post(
        "/servers",
        json={
            "name": "secret-pdf-report-server",
            "source_type": "HTTP",
            "connection_config": {
                "url": "https://example.test/mcp",
                "headers": {"Authorization": "Bearer pdf-secret-token"},
            },
        },
    )
    server = db_session.get(MCPServer, uuid.UUID(server_response.json()["id"]))
    assert server is not None
    audit = _create_audit(db_session, server)

    response = client.get(f"/audits/{audit.id}/report/pdf")

    assert response.status_code == 200
    assert b"pdf-secret-token" not in response.content
    assert b"connection_config" not in response.content
