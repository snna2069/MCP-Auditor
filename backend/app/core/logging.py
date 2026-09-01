"""Structured logging configuration.

Logs are emitted as single-line JSON objects so they can be easily parsed by
log aggregation tools, while remaining human-readable in local development.
"""

import json
import logging
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
            payload["exception"] = self.formatException(record.exc_info)

        extra_keys = set(record.__dict__) - _STANDARD_LOG_RECORD_KEYS
        for key in extra_keys:
            payload[key] = record.__dict__[key]

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
