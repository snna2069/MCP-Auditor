"""Lightweight structured observability primitives.

Metrics are intentionally process-local. Deployment environments can scrape
the endpoint per worker, while the implementation remains dependency-free.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)
request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)


@dataclass
class _Metric:
    count: int = 0
    total_seconds: float = 0.0


class Metrics:
    def __init__(self) -> None:
        self._metrics: dict[tuple[str, tuple[tuple[str, str], ...]], _Metric] = {}
        self._lock = threading.Lock()

    def increment(self, name: str, value: int = 1, **labels: str) -> None:
        with self._lock:
            metric = self._metrics.setdefault((name, _labels(labels)), _Metric())
            metric.count += value

    def observe(self, name: str, value: float, **labels: str) -> None:
        with self._lock:
            metric = self._metrics.setdefault((name, _labels(labels)), _Metric())
            metric.count += 1
            metric.total_seconds += value

    def prometheus(self) -> str:
        with self._lock:
            snapshot = list(self._metrics.items())
        lines: list[str] = []
        for (name, labels), metric in snapshot:
            label_text = _format_labels(labels)
            if metric.total_seconds:
                lines.append(f"{name}_count{label_text} {metric.count}")
                lines.append(f"{name}_sum{label_text} {metric.total_seconds:.6f}")
            else:
                lines.append(f"{name}{label_text} {metric.count}")
        return "\n".join(lines) + ("\n" if lines else "")


metrics = Metrics()


def new_request_id(value: str | None = None) -> str:
    return value if value and len(value) <= 128 else str(uuid.uuid4())


def correlation_fields(**fields: Any) -> dict[str, str]:
    result = {key: str(value) for key, value in fields.items() if value is not None}
    request_id = request_id_context.get()
    if request_id:
        result.setdefault("request_id", request_id)
    return result


def elapsed(start: float) -> float:
    return round(time.monotonic() - start, 6)


def _labels(labels: dict[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(labels.items()))


def _format_labels(labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return ""
    formatted = ",".join(
        f'{key}="{value.replace(chr(34), chr(92) + chr(34))}"' for key, value in labels
    )
    return "{" + formatted + "}"
