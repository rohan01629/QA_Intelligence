"""Structlog configuration and helpers."""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog + stdlib logging for JSON-ish console output."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None, **initial_values: Any) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    logger = structlog.get_logger(name)
    if initial_values:
        return logger.bind(**initial_values)
    return logger


def redact_secrets(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy with sensitive keys redacted."""
    sensitive = {"authorization", "ado_pat", "pat", "password", "token", "secret"}
    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        if key.lower() in sensitive:
            redacted[key] = "***REDACTED***"
        else:
            redacted[key] = value
    return redacted
