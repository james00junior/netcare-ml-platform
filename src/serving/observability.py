"""Structured, privacy-safe logging helpers for inference integration."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

LOGGER_NAME = "netcare.inference"


class JsonFormatter(logging.Formatter):
    """Format operational events as single-line JSON without request payloads."""

    _FIELDS = (
        "event",
        "request_id",
        "method",
        "path",
        "status_code",
        "duration_ms",
        "batch_size",
        "upstream_status",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self._FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        return json.dumps(payload, separators=(",", ":"), default=str)


def get_logger() -> logging.Logger:
    """Return the service logger used by inference integration components."""
    return logging.getLogger(LOGGER_NAME)


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure one JSON stream handler for the service logger."""
    logger = get_logger()
    logger.setLevel(level)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    return logger
