"""Centralized abuse protection for API and expensive operations."""

import hashlib
import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache

import redis
from fastapi import Depends, HTTPException, Request, status

from app.core.config import get_settings


@dataclass(frozen=True)
class RateLimit:
    name: str
    limit: int
    window_seconds: int


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = max(1, retry_after)
        super().__init__("Rate limit exceeded.")


class RateLimiter:
    """Redis-backed fixed-window limiter with an injectable clock/client."""

    def __init__(
        self,
        client: redis.Redis | None = None,
        *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._client = client or redis.Redis.from_url(
            get_settings().redis_url, decode_responses=True
        )
        self._clock = clock

    def check(self, key: str, policy: RateLimit) -> None:
        bucket = int(self._clock() // policy.window_seconds)
        redis_key = f"mcp-auditor:rate:{policy.name}:{_hash_key(key)}:{bucket}"
        try:
            count = int(self._client.incr(redis_key))
            if count == 1:
                self._client.expire(redis_key, policy.window_seconds)
        except redis.RedisError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Abuse protection is temporarily unavailable.",
                headers={"Retry-After": "30"},
            ) from exc

        if count > policy.limit:
            retry_after = policy.window_seconds - (int(self._clock()) % policy.window_seconds)
            raise RateLimitExceeded(retry_after)


@lru_cache
def get_rate_limiter() -> RateLimiter:
    return RateLimiter()


def request_key(request: Request) -> str:
    client = request.client.host if request.client else "unknown"
    return f"{client}:{request.headers.get('x-api-key', '')}"


def enforce_rate_limit(
    request: Request,
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> None:
    settings = get_settings()
    _check(
        limiter,
        request_key(request),
        RateLimit("requests", settings.rate_limit_requests, settings.rate_limit_window_seconds),
    )


def operation_rate_limit(policy_name: str, limit_attr: str):
    def dependency(
        request: Request,
        limiter: RateLimiter = Depends(get_rate_limiter),
    ) -> None:
        settings = get_settings()
        _check(
            limiter,
            request_key(request),
            RateLimit(
                policy_name,
                getattr(settings, limit_attr),
                settings.rate_limit_window_seconds,
            ),
        )

    return dependency


def _check(limiter: RateLimiter, key: str, policy: RateLimit) -> None:
    try:
        limiter.check(key, policy)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please retry later.",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc


def _hash_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
