from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.core import abuse
from app.core.abuse import RateLimiter, RateLimitExceeded


class _FakeRedis:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.expirations: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    def expire(self, key: str, seconds: int) -> bool:
        self.expirations[key] = seconds
        return True


def test_rate_limiter_enforces_fixed_window() -> None:
    limiter = RateLimiter(_FakeRedis(), clock=lambda: 10)
    policy = abuse.RateLimit("audits", 2, 60)

    limiter.check("client", policy)
    limiter.check("client", policy)

    try:
        limiter.check("client", policy)
    except RateLimitExceeded as exc:
        assert exc.retry_after == 50
    else:
        raise AssertionError("expected the third request to be rejected")


def test_rate_limit_dependency_returns_429(client: TestClient, monkeypatch) -> None:
    class Limited:
        def check(self, key: str, policy) -> None:
            raise RateLimitExceeded(17)

    monkeypatch.setattr(
        abuse,
        "get_settings",
        lambda: SimpleNamespace(
            rate_limit_requests=120,
            rate_limit_window_seconds=60,
            rate_limit_discoveries=10,
            rate_limit_audits=5,
            rate_limit_reports=30,
        ),
    )
    from app.main import app

    app.dependency_overrides[abuse.get_rate_limiter] = lambda: Limited()
    response = client.get("/servers")
    assert response.status_code == 429
    assert response.headers["retry-after"] == "17"


def test_audit_creation_is_capped_when_existing_audit_is_active(
    client: TestClient, monkeypatch
) -> None:
    from app.services import audit_service

    monkeypatch.setattr(audit_service.execute_audit_task, "delay", lambda audit_id: None)
    monkeypatch.setattr(
        audit_service,
        "get_settings",
        lambda: SimpleNamespace(max_active_audits_per_server=1),
    )

    server = client.post(
        "/servers",
        json={
            "name": "rate-limited-server",
            "source_type": "MANUAL_CONFIGURATION",
            "connection_config": {},
        },
    ).json()
    first = client.post(f"/servers/{server['id']}/audits")
    assert first.status_code == 202

    second = client.post(f"/servers/{server['id']}/audits")
    assert second.status_code == 429
    assert "active audit" in second.json()["detail"]
