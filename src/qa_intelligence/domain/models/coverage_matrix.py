"""Coverage analysis matrix and result models."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import Field

from qa_intelligence.domain.enums import ScenarioSource
from qa_intelligence.domain.models.base import DomainModel
from qa_intelligence.domain.models.coverage import ScenarioRef

NonEmptyStr = Annotated[str, Field(min_length=1)]


class CoverageStatus(StrEnum):
    """Per-acceptance-criterion coverage status in the matrix."""

    COVERED_BY_TEST = "covered_by_test"
    COVERED_BY_BUG = "covered_by_bug"
    PARTIAL = "partial"
    UNCOVERED = "uncovered"


class AcceptanceCriterionMap(DomainModel):
    """Mapped acceptance criterion intent."""

    ac_id: NonEmptyStr
    order: Annotated[int, Field(ge=1)]
    text: NonEmptyStr


class TestCaseMapEntry(DomainModel):
    """Mapped existing test case inventory entry."""

    test_case_id: Annotated[int, Field(gt=0)]
    title: NonEmptyStr
    steps: list[str] = Field(default_factory=list)
    expected_results: list[str] = Field(default_factory=list)
    state: str = "Unknown"


class BugMapEntry(DomainModel):
    """Mapped related bug inventory entry."""

    bug_id: Annotated[int, Field(gt=0)]
    title: NonEmptyStr
    state: NonEmptyStr
    severity: str | None = None
    repro_steps: str | None = None


class CoverageMatrixRow(DomainModel):
    """One row of the AC × coverage matrix."""

    ac_id: NonEmptyStr
    ac_text: NonEmptyStr
    status: CoverageStatus
    similarity: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    matched_test_case_ids: list[Annotated[int, Field(gt=0)]] = Field(default_factory=list)
    matched_bug_ids: list[Annotated[int, Field(gt=0)]] = Field(default_factory=list)
    explanation: str = ""


class CoverageAnalysisResult(DomainModel):
    """Full coverage analysis with matrix; primary consumer output is uncovered_scenarios."""

    user_story_id: Annotated[int, Field(gt=0)]
    acceptance_criteria: list[AcceptanceCriterionMap] = Field(default_factory=list)
    test_cases: list[TestCaseMapEntry] = Field(default_factory=list)
    bugs: list[BugMapEntry] = Field(default_factory=list)
    matrix: list[CoverageMatrixRow] = Field(default_factory=list)
    uncovered_scenarios: list[ScenarioRef] = Field(
        default_factory=list,
        description="Only uncovered requirement scenarios (primary return)",
    )
    covered_by_test_count: Annotated[int, Field(ge=0)] = 0
    covered_by_bug_count: Annotated[int, Field(ge=0)] = 0
    partial_count: Annotated[int, Field(ge=0)] = 0
    uncovered_count: Annotated[int, Field(ge=0)] = 0
