"""Liveness and dependency readiness endpoints."""

import redis
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.database import engine

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Report basic liveness information for the API."""
    settings = get_settings()
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


@router.get("/ready")
def ready() -> dict[str, str]:
    """Confirm PostgreSQL and Redis are reachable before accepting traffic."""
    settings = get_settings()
    dependencies: dict[str, str] = {}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        dependencies["database"] = "ok"
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "database": type(exc).__name__},
        ) from exc

    client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=2)
    try:
        client.ping()
        dependencies["redis"] = "ok"
    except redis.RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "redis": type(exc).__name__},
        ) from exc
    finally:
        client.close()

    return {"status": "ready", **dependencies}
