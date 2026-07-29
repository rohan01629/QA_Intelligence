"""Test case domain model — exactly three fields."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, field_validator, model_validator

from qa_intelligence.domain.models.base import DomainModel

NonEmptyStr = Annotated[str, Field(min_length=1)]


class TestCase(DomainModel):
    """Executable test case contract used across MCP write paths.

    Contains ONLY:
    - title (Test Title)
    - steps (Test Steps) — array
    - expected_results (Expected Results) — array

    Invariant: ``len(steps) == len(expected_results)``.
    """

    __test__ = False

    title: NonEmptyStr = Field(
        ...,
        description="Test Title",
        examples=["Verify workflow with no tangent added"],
    )
    steps: list[NonEmptyStr] = Field(
        ...,
        min_length=1,
        description="Test Steps — one user action per entry",
    )
    expected_results: list[NonEmptyStr] = Field(
        ...,
        min_length=1,
        description="Expected Results — one assertion per matching step",
    )

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Test Title must not be blank")
        return value.strip()

    @field_validator("steps", "expected_results")
    @classmethod
    def entries_must_be_non_blank(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for index, item in enumerate(values, start=1):
            text = item.strip()
            if not text:
                raise ValueError(f"Entry at position {index} must not be blank")
            cleaned.append(text)
        if not cleaned:
            raise ValueError("Array must contain at least one non-blank entry")
        return cleaned

    @model_validator(mode="after")
    def step_count_must_equal_expected_result_count(self) -> TestCase:
        step_count = len(self.steps)
        expected_result_count = len(self.expected_results)
        if step_count != expected_result_count:
            raise ValueError(
                "step_count must equal expected_result_count "
                f"(steps={step_count}, expected_results={expected_result_count})"
            )
        return self

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def expected_result_count(self) -> int:
        return len(self.expected_results)
