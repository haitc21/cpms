"""Structured logging configuration with secret redaction."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from cpms.observability.redaction import redact_mapping, redact_text


class RedactingJsonFormatter(logging.Formatter):
    """Emit one JSON object per log record with redacted extras."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_text(record.getMessage()),
            "service": getattr(record, "service", "cpms"),
        }
        correlation_id = getattr(record, "correlation_id", None)
        if correlation_id is not None:
            payload["correlation_id"] = correlation_id
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "taskName",
                "service",
                "correlation_id",
            }:
                continue
            payload[key] = redact_mapping(value)
        if record.exc_info:
            payload["exc_info"] = redact_text(self.formatException(record.exc_info))
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", service_name: str = "cpms") -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(RedactingJsonFormatter())
    root.addHandler(handler)
    root.setLevel(level.upper())
    logging.LoggerAdapter(root, {"service": service_name})
