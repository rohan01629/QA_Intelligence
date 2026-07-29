"""Application exception hierarchy for QA Intelligence."""

from __future__ import annotations

from typing import Any


class QaIntelligenceError(Exception):
    """Base error for the application."""

    code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code
        self.message = message
        self.details = details or {}


class DomainValidationError(QaIntelligenceError):
    """Format / invariant validation failure."""

    code = "VALIDATION_ERROR"


class RequirementBlockedError(QaIntelligenceError):
    """Requirement gaps forbid generation."""

    code = "REQUIREMENT_BLOCKED"


class NotFoundError(QaIntelligenceError):
    """Azure DevOps resource not found (404)."""

    code = "ADO_NOT_FOUND"


class AuthError(QaIntelligenceError):
    """Authentication or authorization failure (401/403)."""

    code = "ADO_AUTH_FAILED"


class RateLimitError(QaIntelligenceError):
    """Azure DevOps rate limit (429)."""

    code = "ADO_RATE_LIMITED"

    def __init__(
        self,
        message: str,
        *,
        retry_after_seconds: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)
        self.retry_after_seconds = retry_after_seconds


class UpstreamError(QaIntelligenceError):
    """Upstream 5xx, timeout, or transport failure."""

    code = "ADO_UNAVAILABLE"


class WriteError(QaIntelligenceError):
    """Azure DevOps write (create/link) failure."""

    code = "ADO_WRITE_FAILED"


class ConfigurationError(QaIntelligenceError):
    """Invalid or missing configuration."""

    code = "CONFIG_INVALID"
