import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.mcp.exceptions import MCPConnectionError
from app.mcp.http_client import HttpMCPClient


def test_server_credentials_are_redacted(client: TestClient) -> None:
    response = client.post(
        "/servers",
        json={
            "name": "secret-server",
            "source_type": "HTTP",
            "connection_config": {
                "url": "https://example.com/mcp",
                "headers": {"Authorization": "Bearer real-secret"},
            },
        },
    )
    assert response.status_code == 201
    assert response.json()["connection_config"]["headers"]["Authorization"] == "***"

    server_id = response.json()["id"]
    get_response = client.get(f"/servers/{server_id}")
    assert get_response.json()["connection_config"]["headers"]["Authorization"] == "***"
    assert "real-secret" not in get_response.text


def test_protected_routes_reject_invalid_api_key(client: TestClient) -> None:
    assert client.get("/servers", headers={"X-API-Key": "invalid"}).status_code == 401
    assert client.get("/servers", headers={"X-API-Key": ""}).status_code == 401
    assert TestClient(app).get("/servers").status_code == 401


def test_non_allowlisted_command_is_not_executed(client: TestClient) -> None:
    response = client.post(
        "/servers",
        json={
            "name": "untrusted-command",
            "source_type": "LOCAL_COMMAND",
            "connection_config": {"command": "python", "args": ["-c", "raise SystemExit"]},
        },
    )
    server_id = response.json()["id"]

    discovery = client.post(f"/servers/{server_id}/discover")
    assert discovery.json()["status"] == "FAILED"
    assert discovery.json()["error"] == "Local command is not allowlisted for discovery."


@pytest.mark.parametrize(
    "url",
    ["http://127.0.0.1:8080/mcp", "http://169.254.169.254/latest", "http://[::1]/mcp"],
)
def test_http_client_rejects_private_or_metadata_addresses(url: str) -> None:
    with pytest.raises(MCPConnectionError):
        HttpMCPClient(url)


def test_missing_server_still_returns_not_found(client: TestClient) -> None:
    response = client.get(f"/servers/{uuid.uuid4()}")
    assert response.status_code == 404
