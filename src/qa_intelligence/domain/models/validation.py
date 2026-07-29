"""Validation result domain model."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, model_validator

from qa_intelligence.domain.models.base import DomainModel

NonEmptyStr = Annotated[str, Field(min_length=1)]


class ValidationIssue(DomainModel):
    """A single validation error or warning."""

    code: NonEmptyStr
    message: NonEmptyStr
    field: str | None = None
    details: dict[str, object] = Field(default_factory=dict)


class ValidationResult(DomainModel):
    """Outcome of validating a domain object (typically a TestCase)."""

    is_valid: bool
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)

    @model_validator(mode="after")
    def validity_must_match_errors(self) -> ValidationResult:
        if self.is_valid and self.errors:
            raise ValueError("is_valid cannot be true when errors are present")
        if not self.is_valid and not self.errors:
            raise ValueError("is_valid cannot be false when errors are empty")
        return self

    @classmethod
    def success(cls, warnings: list[ValidationIssue] | None = None) -> ValidationResult:
        return cls(is_valid=True, errors=[], warnings=warnings or [])

    @classmethod
    def failure(
        cls,
        errors: list[ValidationIssue],
        warnings: list[ValidationIssue] | None = None,
    ) -> ValidationResult:
        if not errors:
            raise ValueError("failure requires at least one error")
        return cls(is_valid=False, errors=errors, warnings=warnings or [])
