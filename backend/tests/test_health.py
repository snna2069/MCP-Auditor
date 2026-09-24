"""Smoke tests for the API."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.api import health as health_api


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "app_name" in body
    assert "version" in body


def test_ready_reports_dependency_health(client: TestClient, monkeypatch) -> None:
    class RedisClient:
        def ping(self) -> bool:
            return True

        def close(self) -> None:
            return None

    readiness_engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(health_api, "engine", readiness_engine)
    monkeypatch.setattr(health_api.redis.Redis, "from_url", lambda *args, **kwargs: RedisClient())

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok", "redis": "ok"}
