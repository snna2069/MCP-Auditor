"""FastAPI application entry point."""

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.observability import (
    correlation_fields,
    elapsed,
    metrics,
    new_request_id,
    request_id_context,
)

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.observability_log_level or settings.log_level)
    logger.info(
        "starting application",
        extra={"app_env": settings.app_env, "app_version": settings.app_version},
    )
    yield
    logger.info("shutting down application")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


@app.middleware("http")
async def request_observability(request: Request, call_next) -> Response:
    request_id = new_request_id(request.headers.get("X-Request-ID"))
    token = request_id_context.set(request_id)
    started = time.monotonic()
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        metrics.observe(
            "http_request_duration_seconds",
            elapsed(started),
            method=request.method,
            route=request.url.path,
        )
        logger.info(
            "http request completed",
            extra=correlation_fields(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_seconds=elapsed(started),
            ),
        )
        return response
    except Exception:
        metrics.increment("http_request_failures_total", method=request.method)
        logger.exception(
            "http request failed",
            extra=correlation_fields(method=request.method, path=request.url.path),
        )
        raise
    finally:
        request_id_context.reset(token)


@app.get("/metrics", include_in_schema=False)
def metrics_endpoint() -> Response:
    return Response(metrics.prometheus(), media_type="text/plain; version=0.0.4")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
