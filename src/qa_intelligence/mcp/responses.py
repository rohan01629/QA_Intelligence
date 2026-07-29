"""Map application errors to MCP ToolResponse envelopes."""

from __future__ import annotations

import structlog
from pydantic import ValidationError

from qa_intelligence.infrastructure.errors import QaIntelligenceError
from qa_intelligence.mcp.schemas.common import ErrorBody, ToolResponse
from qa_intelligence.prompts.analysis_guidance import generation_guidance, product_rules_guidance

logger = structlog.get_logger(__name__)


def success(data: object, *, warnings: list[str] | None = None) -> ToolResponse:
    return ToolResponse(ok=True, data=_serialize(data), warnings=warnings or [])


def failure(
    code: str,
    message: str,
    *,
    details: dict[str, object] | None = None,
    warnings: list[str] | None = None,
) -> ToolResponse:
    return ToolResponse(
        ok=False,
        error=ErrorBody(code=code, message=message, details=details),
        warnings=warnings or [],
    )


def from_exception(exc: BaseException, *, tool_name: str) -> ToolResponse:
    """Convert known errors into a structured ToolResponse; log unknowns."""
    if isinstance(exc, QaIntelligenceError):
        return failure(exc.code, exc.message, details=exc.details or None)

    if isinstance(exc, ValidationError):
        return failure(
            "VALIDATION_ERROR",
            "Request or payload validation failed",
            details={"errors": exc.errors()},
        )

    if isinstance(exc, ValueError):
        return failure("VALIDATION_ERROR", str(exc) or "Invalid value")

    logger.exception("mcp.tool_failed", tool=tool_name, error=str(exc))
    return failure(
        "INTERNAL_ERROR",
        f"{tool_name} failed unexpectedly",
        details={"error_type": type(exc).__name__},
    )


def with_guidance(response: ToolResponse, *, generation: bool = False) -> ToolResponse:
    """Attach product-rule guidance as soft warnings when useful."""
    text = generation_guidance() if generation else product_rules_guidance()
    if text and text not in response.warnings:
        response.warnings = [*response.warnings, text]
    return response


def _serialize(data: object) -> object:
    if data is None:
        return None
    if hasattr(data, "model_dump"):
        return data.model_dump(mode="json")  # type: ignore[no-any-return]
    if isinstance(data, list):
        return [_serialize(item) for item in data]
    if isinstance(data, dict):
        return {key: _serialize(value) for key, value in data.items()}
    return data
