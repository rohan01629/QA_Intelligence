"""Feature and requirement analysis models."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, model_validator

from qa_intelligence.domain.enums import (
    FeatureType,
    GapSeverity,
    RequirementGapType,
    RiskLevel,
    TestCategory,
)
from qa_intelligence.domain.models.base import DomainModel
from qa_intelligence.domain.models.qa_strategy import QAStrategy

NonEmptyStr = Annotated[str, Field(min_length=1)]


class RequirementGap(DomainModel):
    """Incomplete or conflicting requirement finding."""

    type: RequirementGapType
    severity: GapSeverity
    description: NonEmptyStr
    evidence: str = ""


class FeatureAnalysis(DomainModel):
    """Structured understanding of the feature before QA Strategy finalization."""

    feature_type: FeatureType
    risk_level: RiskLevel
    business_rules: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    modules: list[str] = Field(default_factory=list)
    validation_rules: list[str] = Field(default_factory=list)
    data_flow_notes: str | None = None
    regression_impact: str | None = None
    applicable_optional_categories: list[TestCategory] = Field(default_factory=list)
    excluded_optional_categories: list[TestCategory] = Field(default_factory=list)
    rationale: NonEmptyStr = Field(
        ...,
        description="Why this feature type / risk / category split applies",
    )

    @model_validator(mode="after")
    def optional_category_sets_must_be_disjoint(self) -> FeatureAnalysis:
        overlap = set(self.applicable_optional_categories).intersection(
            self.excluded_optional_categories
        )
        if overlap:
            names = ", ".join(sorted(c.value for c in overlap))
            raise ValueError(
                f"applicable and excluded optional categories must be disjoint; overlap: {names}"
            )
        return self


class RequirementAnalysis(DomainModel):
    """Full requirement analysis including gaps and QA Strategy."""

    user_story_id: Annotated[int, Field(gt=0)]
    feature_analysis: FeatureAnalysis
    requirement_gaps: list[RequirementGap] = Field(default_factory=list)
    qa_strategy: QAStrategy
    blocked: bool = False

    @model_validator(mode="after")
    def blocked_flags_must_align(self) -> RequirementAnalysis:
        has_blocking_gap = any(
            gap.severity == GapSeverity.BLOCKING for gap in self.requirement_gaps
        )
        if has_blocking_gap and not self.blocked:
            raise ValueError(
                "blocked must be true when any requirement gap has severity=blocking"
            )
        if self.blocked != self.qa_strategy.blocked:
            raise ValueError("blocked must match qa_strategy.blocked")
        return self

    @property
    def business_rules(self) -> list[str]:
        return self.feature_analysis.business_rules

    @property
    def dependencies(self) -> list[str]:
        return self.feature_analysis.dependencies

    @property
    def modules(self) -> list[str]:
        return self.feature_analysis.modules
