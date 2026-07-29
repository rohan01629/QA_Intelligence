"""Test strategy domain models — category decisions and risk-based plan."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from qa_intelligence.domain.enums import (
    FeatureType,
    GenerationDirective,
    RiskLevel,
    TestCategory,
)
from qa_intelligence.domain.models.base import DomainModel
from qa_intelligence.domain.models.qa_strategy import CoverageEstimates, QAStrategy

NonEmptyStr = Annotated[str, Field(min_length=1)]
NonNegativeInt = Annotated[int, Field(ge=0)]


class CategoryDecision(DomainModel):
    """Single category include/skip decision with auditable reason."""

    category: TestCategory
    applicable: bool
    reason: NonEmptyStr
    priority: RiskLevel = RiskLevel.MEDIUM


class RiskBasedTestingStrategy(DomainModel):
    """How deeply / in what order to apply applicable categories given risk."""

    risk_level: RiskLevel
    focus_areas: list[str] = Field(default_factory=list)
    depth_guidance: NonEmptyStr
    regression_emphasis: NonEmptyStr
    priority_order: list[TestCategory] = Field(default_factory=list)
    recommended_cases_per_uncovered_scenario: Annotated[float, Field(gt=0)] = 1.0


class TestStrategy(DomainModel):
    """Final testing strategy — categories, skips, estimates, risk plan.

    Does not contain generated test cases.
    """

    __test__ = False

    user_story_id: Annotated[int, Field(gt=0)]
    feature_type: FeatureType
    risk_level: RiskLevel
    applicable_categories: list[CategoryDecision] = Field(default_factory=list)
    skipped_categories: list[CategoryDecision] = Field(default_factory=list)
    estimated_new_test_cases: NonNegativeInt = 0
    estimated_existing_coverage: NonNegativeInt = 0
    estimated_duplicate_scenarios: NonNegativeInt = 0
    risk_based_strategy: RiskBasedTestingStrategy
    narrative_summary: NonEmptyStr
    blocked: bool = False
    generation_directive: GenerationDirective = GenerationDirective.GAP_FILL_ONLY
    estimates: CoverageEstimates = Field(default_factory=CoverageEstimates)
    qa_strategy: QAStrategy
