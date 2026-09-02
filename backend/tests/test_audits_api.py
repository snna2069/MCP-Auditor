"""End-to-end tests for the audit execution API.

Celery runs in eager mode during tests (see conftest.py), so
POST /servers/{id}/audits completes synchronously and the response
already reflects the final COMPLETED/FAILED state - a real deployment
returns PENDING immediately and the client polls GET /audits/{id}.
"""

import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

FAKE_SERVER_PATH = str(Path(__file__).parent / "fixtures" / "fake_stdio_server.py")


def _create_manual_server(client: TestClient, tools: list[dict]) -> str:
    response = client.post(
        "/servers",
        json={
            "name": "manual-audit-target",
            "source_type": "MANUAL_CONFIGURATION",
            "connection_config": {"details": {"tools": tools}},
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_audit_completes_and_produces_findings_for_risky_tool(client: TestClient) -> None:
    server_id = _create_manual_server(
        client,
        [
            {
                "name": "delete_file",
                "description": "Deletes a file from disk.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                },
            }
        ],
    )

    response = client.post(f"/servers/{server_id}/audits")
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["overall_score"] is not None
    assert body["overall_score"] < 100.0
    assert body["risk_level"] is not None
    assert body["error_message"] is None
    assert body["started_at"] is not None
    assert body["completed_at"] is not None

    audit_id = body["id"]

    get_response = client.get(f"/audits/{audit_id}")
    assert get_response.status_code == 200
    detail = get_response.json()
    assert detail["status"] == "COMPLETED"
    assert detail["category_scores"]["TOOL_DEFINITION_QUALITY"] < 100.0
    assert sum(detail["severity_breakdown"].values()) == len(
        client.get(f"/audits/{audit_id}/findings").json()
    )
    assert len(detail["score_contributors"]) > 0
    assert detail["score_contributors"][0]["contribution"] > 0

    findings_response = client.get(f"/audits/{audit_id}/findings")
    assert findings_response.status_code == 200
    findings = findings_response.json()
    assert len(findings) > 0
    assert any(
        f["title"] == "Tool description does not disclose destructive behavior" for f in findings
    )


def test_audit_with_no_tools_completes_with_perfect_score(client: TestClient) -> None:
    server_id = _create_manual_server(client, [])

    response = client.post(f"/servers/{server_id}/audits")
    assert response.status_code == 202
    body = response.json()

    assert body["status"] == "COMPLETED"
    assert body["overall_score"] == 100.0
    assert body["risk_level"] == "LOW"

    findings_response = client.get(f"/audits/{body['id']}/findings")
    assert findings_response.json() == []


def test_audit_for_missing_server_returns_404(client: TestClient) -> None:
    response = client.post(f"/servers/{uuid.uuid4()}/audits")
    assert response.status_code == 404


def test_audit_fails_fast_when_broker_is_unavailable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If enqueueing itself fails (e.g. Redis unreachable), the audit must
    be marked FAILED immediately rather than hanging the request or being
    left stuck PENDING forever."""
    server_id = _create_manual_server(client, [])

    def _boom(*_args, **_kwargs):
        raise ConnectionError("could not connect to broker")

    monkeypatch.setattr("app.services.audit_service.execute_audit_task.delay", _boom)

    response = client.post(f"/servers/{server_id}/audits")
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "FAILED"
    assert "worker" in body["error_message"].lower()


def test_audit_detail_score_breakdown_is_none_before_completion(client: TestClient) -> None:
    create_response = client.post(
        "/servers",
        json={
            "name": "broken-audit-target-2",
            "source_type": "LOCAL_COMMAND",
            "connection_config": {
                "command": "this-command-does-not-exist-anywhere",
                "args": [],
            },
        },
    )
    server_id = create_response.json()["id"]

    response = client.post(f"/servers/{server_id}/audits")
    body = response.json()
    assert body["status"] == "FAILED"

    detail = client.get(f"/audits/{body['id']}").json()
    assert detail["category_scores"] is None
    assert detail["severity_breakdown"] is None
    assert detail["score_contributors"] is None


def test_audit_for_unreachable_local_command_server_fails(client: TestClient) -> None:
    create_response = client.post(
        "/servers",
        json={
            "name": "broken-audit-target",
            "source_type": "LOCAL_COMMAND",
            "connection_config": {
                "command": "this-command-does-not-exist-anywhere",
                "args": [],
            },
        },
    )
    assert create_response.status_code == 201
    server_id = create_response.json()["id"]

    response = client.post(f"/servers/{server_id}/audits")
    assert response.status_code == 202
    body = response.json()

    assert body["status"] == "FAILED"
    assert body["error_message"] is not None
    assert body["overall_score"] is None
    assert body["risk_level"] is None

    findings_response = client.get(f"/audits/{body['id']}/findings")
    assert findings_response.json() == []


def test_list_audits_returns_created_audits(client: TestClient) -> None:
    server_id = _create_manual_server(client, [])
    client.post(f"/servers/{server_id}/audits")
    client.post(f"/servers/{server_id}/audits")

    response = client.get("/audits")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_audits_filters_by_server_id(client: TestClient) -> None:
    server_a = _create_manual_server(client, [])
    server_b = _create_manual_server(client, [])
    client.post(f"/servers/{server_a}/audits")
    client.post(f"/servers/{server_b}/audits")

    response = client.get(f"/audits?server_id={server_a}")
    assert response.status_code == 200
    audits = response.json()
    assert len(audits) == 1
    assert audits[0]["server_id"] == server_a


def test_get_missing_audit_returns_404(client: TestClient) -> None:
    response = client.get(f"/audits/{uuid.uuid4()}")
    assert response.status_code == 404


def test_list_findings_for_missing_audit_returns_404(client: TestClient) -> None:
    response = client.get(f"/audits/{uuid.uuid4()}/findings")
    assert response.status_code == 404


def test_audit_runs_fresh_discovery_via_local_command(client: TestClient) -> None:
    """Confirms the pipeline re-discovers (not just reuses stale data)."""
    import json

    scenario = json.dumps(
        {
            "tools": [
                {
                    "name": "get_time",
                    "description": "Returns the current time.",
                    "inputSchema": {"type": "object"},
                }
            ]
        }
    )
    create_response = client.post(
        "/servers",
        json={
            "name": "local-audit-target",
            "source_type": "LOCAL_COMMAND",
            "connection_config": {
                "command": sys.executable,
                "args": [FAKE_SERVER_PATH],
                "env": {"FAKE_MCP_SCENARIO": scenario},
            },
        },
    )
    assert create_response.status_code == 201
    server_id = create_response.json()["id"]

    response = client.post(f"/servers/{server_id}/audits")
    assert response.status_code == 202
    body = response.json()

    assert body["status"] == "COMPLETED"

    findings = client.get(f"/audits/{body['id']}/findings").json()
    assert any(f["tool_name"] == "get_time" for f in findings)
