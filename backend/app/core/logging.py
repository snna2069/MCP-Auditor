"""Structured logging configuration.

Logs are emitted as single-line JSON objects so they can be easily parsed by
log aggregation tools, while remaining human-readable in local development.
"""

import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """Format log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception_type"] = record.exc_info[0].__name__

        extra_keys = set(record.__dict__) - _STANDARD_LOG_RECORD_KEYS
        for key in extra_keys:
            if key not in {"args", "exc_text", "stack_info"} and not _sensitive(key):
                payload[key] = _safe_value(record.__dict__[key])

        return json.dumps(payload, default=str)


_STANDARD_LOG_RECORD_KEYS = set(
    logging.LogRecord(
        name="",
        level=0,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None,
    ).__dict__
)
_SENSITIVE_PATTERN = re.compile(
    r"(password|secret|token|api[_-]?key|credential|authorization|cookie|private[_-]?key)",
    re.IGNORECASE,
)


def _sensitive(value: str) -> bool:
    return bool(_SENSITIVE_PATTERN.search(value))


def _safe_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if _sensitive(str(key)) else _safe_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_safe_value(item) for item in value[:20]]
    if isinstance(value, str) and len(value) > 512:
        return value[:512] + "...[TRUNCATED]"
    return value


def configure_logging(log_level: str = "INFO") -> None:
    """Configure root logging handlers with a JSON formatter."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # Keep noisy third-party loggers at a reasonable level.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
