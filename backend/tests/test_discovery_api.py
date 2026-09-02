"""End-to-end tests for the discovery API endpoints."""

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

FAKE_SERVER_PATH = str(Path(__file__).parent / "fixtures" / "fake_stdio_server.py")


def _create_manual_server_with_tools(client: TestClient) -> str:
    response = client.post(
        "/servers",
        json={
            "name": "manual-with-tools",
            "source_type": "MANUAL_CONFIGURATION",
            "connection_config": {
                "details": {
                    "tools": [
                        {
                            "name": "lookup_order",
                            "description": "Looks up an order by id",
                            "inputSchema": {"type": "object"},
                        }
                    ]
                }
            },
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_discover_manual_server_persists_tools(client: TestClient) -> None:
    server_id = _create_manual_server_with_tools(client)

    response = client.post(f"/servers/{server_id}/discover")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUCCESS"
    assert body["tool_count"] == 1
    assert body["tools"][0]["name"] == "lookup_order"

    tools_response = client.get(f"/servers/{server_id}/tools")
    assert tools_response.status_code == 200
    assert len(tools_response.json()) == 1
    assert tools_response.json()[0]["name"] == "lookup_order"


def test_tools_endpoint_empty_before_discovery(client: TestClient) -> None:
    server_id = _create_manual_server_with_tools(client)

    response = client.get(f"/servers/{server_id}/tools")
    assert response.status_code == 200
    assert response.json() == []


def test_discover_local_command_server_succeeds(client: TestClient) -> None:
    scenario = json.dumps(
        {
            "tools": [
                {
                    "name": "get_time",
                    "description": "Returns the current time",
                    "inputSchema": {"type": "object"},
                }
            ]
        }
    )
    create_response = client.post(
        "/servers",
        json={
            "name": "local-fake-server",
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

    response = client.post(f"/servers/{server_id}/discover")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUCCESS"
    assert body["tool_count"] == 1
    assert body["tools"][0]["name"] == "get_time"


def test_discover_local_command_server_reports_failure(client: TestClient) -> None:
    create_response = client.post(
        "/servers",
        json={
            "name": "broken-local-server",
            "source_type": "LOCAL_COMMAND",
            "connection_config": {
                "command": "this-command-does-not-exist-anywhere",
                "args": [],
            },
        },
    )
    assert create_response.status_code == 201
    server_id = create_response.json()["id"]

    response = client.post(f"/servers/{server_id}/discover")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FAILED"
    assert body["error"] is not None
    assert body["tool_count"] == 0


def test_discover_missing_server_returns_404(client: TestClient) -> None:
    import uuid

    response = client.post(f"/servers/{uuid.uuid4()}/discover")
    assert response.status_code == 404


def test_list_tools_for_missing_server_returns_404(client: TestClient) -> None:
    import uuid

    response = client.get(f"/servers/{uuid.uuid4()}/tools")
    assert response.status_code == 404
