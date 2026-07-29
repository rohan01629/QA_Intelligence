"""Infrastructure adapters: config, logging, errors.

Import Container/build_container from qa_intelligence.infrastructure.di
to avoid circular imports with the services package.
"""

from __future__ import annotations

from qa_intelligence.infrastructure.config import Settings, clear_settings_cache, get_settings
from qa_intelligence.infrastructure.errors import (
    AuthError,
    ConfigurationError,
    DomainValidationError,
    NotFoundError,
    QaIntelligenceError,
    RateLimitError,
    RequirementBlockedError,
    UpstreamError,
    WriteError,
)
from qa_intelligence.infrastructure.logging import configure_logging, get_logger

__all__ = [
    "AuthError",
    "ConfigurationError",
    "DomainValidationError",
    "NotFoundError",
    "QaIntelligenceError",
    "RateLimitError",
    "RequirementBlockedError",
    "Settings",
    "UpstreamError",
    "WriteError",
    "clear_settings_cache",
    "configure_logging",
    "get_logger",
    "get_settings",
]
