"""Shared pytest fixtures."""

import os

# Ensure a valid Fernet key is present before any app module reads settings,
# regardless of whether a local .env file defines one. Set only if unset so
# a developer's real .env value (if present) still takes precedence.
os.environ.setdefault("ENCRYPTION_KEY", "MTi6-EPnzQZbqxv82PJU2BwHcw92h4f9C1nDZZnlEJA=")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import database
from app.core.database import get_db
from app.main import app
from app.models import Base
from app.workers.celery_app import celery_app

# Audits are triggered via Celery's `.delay()`. Running eagerly (in-process,
# no broker/worker required) keeps tests deterministic and independent of
# any real Redis instance - a standard, documented Celery testing pattern.
celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)


@pytest.fixture
def db_session(monkeypatch: pytest.MonkeyPatch):
    """A SQLite in-memory database, isolated per test.

    Also patches app.core.database.SessionLocal so a Celery task executed
    eagerly during a test (see app/workers/audit_worker.py) reads/writes
    the same in-memory database as the API request that triggered it.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session_local = sessionmaker(
        bind=engine, autocommit=False, autoflush=False, future=True
    )
    monkeypatch.setattr(database, "SessionLocal", testing_session_local)

    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
