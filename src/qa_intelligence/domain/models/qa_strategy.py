"""QA Strategy and category decision models."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, model_validator

from qa_intelligence.domain.enums import FeatureType, RiskLevel, TestCategory
from qa_intelligence.domain.models.base import DomainModel

NonEmptyStr = Annotated[str, Field(min_length=1)]
NonNegativeInt = Annotated[int, Field(ge=0)]


class CategoryExclusion(DomainModel):
    """A test category explicitly excluded from generation."""

    category: TestCategory
    reason: NonEmptyStr


class CoverageEstimates(DomainModel):
    """Estimated coverage budget for generation."""

    estimated_new_test_cases: NonNegativeInt = 0
    estimated_existing_coverage: NonNegativeInt = 0
    estimated_duplicate_scenarios: NonNegativeInt = 0
    preliminary: bool = True


class QAStrategy(DomainModel):
    """Decision record: what to test, what to skip, and coverage estimates."""

    feature_type: FeatureType
    risk: RiskLevel
    testing_required: list[TestCategory] = Field(min_length=1)
    testing_not_required: list[CategoryExclusion] = Field(default_factory=list)
    reason: NonEmptyStr
    estimates: CoverageEstimates = Field(default_factory=CoverageEstimates)
    blocked: bool = False

    @model_validator(mode="after")
    def required_and_excluded_must_be_disjoint(self) -> QAStrategy:
        excluded = {item.category for item in self.testing_not_required}
        overlap = excluded.intersection(self.testing_required)
        if overlap:
            names = ", ".join(sorted(c.value for c in overlap))
            raise ValueError(
                f"testing_required and testing_not_required must be disjoint; overlap: {names}"
            )
        return self

    @model_validator(mode="after")
    def blocked_implies_zero_new_estimates(self) -> QAStrategy:
        if self.blocked and self.estimates.estimated_new_test_cases != 0:
            raise ValueError(
                "when blocked is true, estimated_new_test_cases must be 0"
            )
        return self
