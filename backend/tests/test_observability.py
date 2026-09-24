from fastapi.testclient import TestClient

from app.core.logging import JSONFormatter


def test_requests_are_correlated_and_metrics_are_exposed(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "request-test-1"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "request-test-1"
    metrics_text = client.get("/metrics").text
    assert "http_request_duration_seconds_count" in metrics_text


def test_structured_formatter_redacts_sensitive_fields() -> None:
    import logging

    record = logging.LogRecord("test", logging.INFO, __file__, 1, "safe", (), None)
    record.api_token = "do-not-log"
    record.details = {"password": "do-not-log", "count": 1}

    output = JSONFormatter().format(record)

    assert "do-not-log" not in output
    assert "[REDACTED]" in output
