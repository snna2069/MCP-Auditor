"""Celery application instance.

Kept minimal per the project's "start with a simple worker architecture"
guidance: one broker, one task module. Run a worker with:

    celery -A app.workers.celery_app worker --loglevel=info

In tests (see tests/conftest.py), task_always_eager is set to True so
audits execute synchronously in-process, without needing a running
broker/worker - a standard, documented Celery testing pattern.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "mcp_server_auditor",
    broker=settings.redis_url,
    # No result backend: Audit status/results are tracked in our own
    # database (see app.models.audit), not via Celery's result store. A
    # configured result backend would otherwise maintain its own
    # persistent, independently-retrying connection even when idle.
    include=["app.workers.audit_worker"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_ignore_result=True,
    # Fail fast rather than retrying for ~20 attempts (Celery/kombu's
    # default) if the broker is unreachable: enqueueing a task happens
    # synchronously during the POST /servers/{id}/audits request, so a slow
    # broker would otherwise hang that HTTP request for a long time.
    broker_connection_retry_on_startup=False,
    broker_connection_retry=False,
    broker_connection_timeout=2,
)
