"""Test case generation result models."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import Field

from qa_intelligence.domain.enums import GenerationDirective, TestCategory
from qa_intelligence.domain.models.base import DomainModel
from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.domain.models.validation import ValidationResult

NonEmptyStr = Annotated[str, Field(min_length=1)]


class GenerationMode(StrEnum):
    FRESH_SUITE = "fresh_suite"
    GAP_FILL_ONLY = "gap_fill_only"
    BLOCKED = "blocked"


class GeneratedTestCaseRecord(DomainModel):
    """One generation attempt with validation outcome."""

    __test__ = False

    source_scenario_key: NonEmptyStr
    category: TestCategory
    test_case: TestCase | None = None
    validation: ValidationResult
    rejected: bool = False


class TestCaseGenerationResult(DomainModel):
    """Output of TestCaseGenerationService — valid cases only in ``generated``."""

    __test__ = False

    user_story_id: Annotated[int, Field(gt=0)]
    mode: GenerationMode
    generation_directive: GenerationDirective
    generated: list[TestCase] = Field(default_factory=list)
    records: list[GeneratedTestCaseRecord] = Field(default_factory=list)
    rejected_count: Annotated[int, Field(ge=0)] = 0
    blocked: bool = False
    notes: str = ""
