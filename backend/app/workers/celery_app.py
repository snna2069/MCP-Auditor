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
    backend=settings.redis_url,
    include=["app.workers.audit_worker"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
