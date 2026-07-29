"""Shared MCP tool response envelope."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    """Machine-readable tool error."""

    code: str
    message: str
    details: dict[str, Any] | None = None


class ToolResponse(BaseModel):
    """Standard response returned by every QA Intelligence MCP tool."""

    ok: bool
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    data: Any | None = None
    error: ErrorBody | None = None
    warnings: list[str] = Field(default_factory=list)

    @classmethod
    def not_implemented(cls, tool_name: str) -> ToolResponse:
        """Stub response until service logic is wired."""
        return cls(
            ok=False,
            error=ErrorBody(
                code="NOT_IMPLEMENTED",
                message=f"{tool_name} is registered but not implemented yet",
                details={"tool": tool_name},
            ),
        )
