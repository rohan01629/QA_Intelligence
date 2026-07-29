"""Test case format validation helpers."""

from __future__ import annotations

from pydantic import ValidationError

from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.domain.models.validation import ValidationIssue, ValidationResult


def validate_test_case_payload(payload: dict[str, object]) -> tuple[TestCase | None, ValidationResult]:
    """Validate a raw test-case dict; reject on any invariant failure."""
    try:
        case = TestCase.model_validate(payload)
    except ValidationError as exc:
        errors = [_issue_from_pydantic(err) for err in exc.errors()]
        if not errors:
            errors = [
                ValidationIssue(
                    code="VALIDATION_ERROR",
                    message="Test case failed validation",
                )
            ]
        return None, ValidationResult.failure(errors)

    # Explicit parity guard (also enforced by model).
    if case.step_count != case.expected_result_count:
        return None, ValidationResult.failure(
            [
                ValidationIssue(
                    code="VALIDATION_STEP_MISMATCH",
                    message=(
                        "step_count must equal expected_result_count "
                        f"(steps={case.step_count}, expected_results={case.expected_result_count})"
                    ),
                    field="steps",
                    details={
                        "step_count": case.step_count,
                        "expected_result_count": case.expected_result_count,
                    },
                )
            ]
        )
    return case, ValidationResult.success()


def _issue_from_pydantic(error: dict[str, object]) -> ValidationIssue:
    loc = error.get("loc") or ()
    field = ".".join(str(part) for part in loc) if loc else None
    msg = str(error.get("msg") or "Invalid value")
    code = "VALIDATION_ERROR"
    lowered = msg.lower()
    if "step_count" in lowered or "expected_result_count" in lowered:
        code = "VALIDATION_STEP_MISMATCH"
    elif "title" in (field or "") and "blank" in lowered:
        code = "VALIDATION_BLANK_TITLE"
    elif "steps" in (field or "") and ("at least" in lowered or "empty" in lowered):
        code = "VALIDATION_EMPTY_STEPS"
    elif "expected_results" in (field or "") and (
        "at least" in lowered or "empty" in lowered
    ):
        code = "VALIDATION_EMPTY_EXPECTED"
    elif error.get("type") == "extra_forbidden":
        code = "VALIDATION_EXTRA_FIELDS"
    return ValidationIssue(code=code, message=msg, field=field, details={"type": error.get("type")})
