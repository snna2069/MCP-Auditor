"""Tests for MCP server registration endpoints."""

import uuid

from fastapi.testclient import TestClient


def test_create_and_get_http_server(client: TestClient) -> None:
    payload = {
        "name": "weather-mcp",
        "source_type": "HTTP",
        "connection_config": {
            "url": "https://example.com/mcp",
            "headers": {"Authorization": "Bearer secret-token"},
        },
    }

    create_response = client.post("/servers", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "weather-mcp"
    assert created["source_type"] == "HTTP"
    assert created["connection_config"]["url"] == "https://example.com/mcp"
    assert created["connection_config"]["headers"]["Authorization"] == ("Bearer secret-token")
    assert created["connection_config"]["timeout_seconds"] == 30

    get_response = client.get(f"/servers/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json() == created


def test_create_local_command_server(client: TestClient) -> None:
    payload = {
        "name": "local-fs-tool",
        "source_type": "LOCAL_COMMAND",
        "connection_config": {"command": "python", "args": ["server.py"]},
    }

    response = client.post("/servers", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["connection_config"]["command"] == "python"
    assert body["connection_config"]["args"] == ["server.py"]
    assert body["connection_config"]["env"] == {}


def test_create_manual_configuration_server(client: TestClient) -> None:
    payload = {
        "name": "manual-entry",
        "source_type": "MANUAL_CONFIGURATION",
        "connection_config": {
            "description": "Documented via vendor PDF",
            "details": {"vendor": "Acme"},
        },
    }

    response = client.post("/servers", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["connection_config"]["description"] == "Documented via vendor PDF"


def test_create_server_with_mismatched_config_fails(client: TestClient) -> None:
    payload = {
        "name": "bad-http",
        "source_type": "HTTP",
        # missing required "url"
        "connection_config": {"headers": {}},
    }

    response = client.post("/servers", json=payload)
    assert response.status_code == 422


def test_create_server_with_unsupported_source_type_fails(client: TestClient) -> None:
    payload = {
        "name": "not-yet-supported",
        "source_type": "SSE",
        "connection_config": {},
    }

    response = client.post("/servers", json=payload)
    assert response.status_code == 422


def test_list_servers_returns_created_servers(client: TestClient) -> None:
    for name in ("server-a", "server-b"):
        client.post(
            "/servers",
            json={
                "name": name,
                "source_type": "MANUAL_CONFIGURATION",
                "connection_config": {},
            },
        )

    response = client.get("/servers")
    assert response.status_code == 200
    names = {server["name"] for server in response.json()}
    assert names == {"server-a", "server-b"}


def test_get_missing_server_returns_404(client: TestClient) -> None:
    response = client.get(f"/servers/{uuid.uuid4()}")
    assert response.status_code == 404


def test_delete_server(client: TestClient) -> None:
    create_response = client.post(
        "/servers",
        json={
            "name": "to-delete",
            "source_type": "MANUAL_CONFIGURATION",
            "connection_config": {},
        },
    )
    server_id = create_response.json()["id"]

    delete_response = client.delete(f"/servers/{server_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/servers/{server_id}")
    assert get_response.status_code == 404


def test_delete_missing_server_returns_404(client: TestClient) -> None:
    response = client.delete(f"/servers/{uuid.uuid4()}")
    assert response.status_code == 404
