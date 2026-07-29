"""Coverage report domain models."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, model_validator

from qa_intelligence.domain.enums import (
    GenerationDirective,
    ScenarioSource,
    TestCategory,
)
from qa_intelligence.domain.models.base import DomainModel
from qa_intelligence.domain.models.qa_strategy import QAStrategy

NonEmptyStr = Annotated[str, Field(min_length=1)]


class ScenarioRef(DomainModel):
    """Reference to a covered, missing, duplicate, or bug-covered scenario."""

    key: NonEmptyStr
    title: NonEmptyStr
    category: TestCategory | None = None
    source: ScenarioSource
    related_ids: list[Annotated[int, Field(gt=0)]] = Field(default_factory=list)


class CoverageReport(DomainModel):
    """Coverage analysis output used to drive gap-only generation."""

    user_story_id: Annotated[int, Field(gt=0)]
    covered_scenarios: list[ScenarioRef] = Field(default_factory=list)
    duplicate_scenarios: list[ScenarioRef] = Field(default_factory=list)
    bug_covered_scenarios: list[ScenarioRef] = Field(default_factory=list)
    missing_scenarios: list[ScenarioRef] = Field(default_factory=list)
    qa_strategy_final: QAStrategy
    generation_directive: GenerationDirective

    @model_validator(mode="after")
    def blocked_directive_aligns_with_strategy(self) -> CoverageReport:
        if (
            self.qa_strategy_final.blocked
            and self.generation_directive != GenerationDirective.BLOCKED
        ):
            raise ValueError(
                "generation_directive must be blocked when qa_strategy_final.blocked is true"
            )
        if (
            self.generation_directive == GenerationDirective.BLOCKED
            and not self.qa_strategy_final.blocked
        ):
            raise ValueError(
                "qa_strategy_final.blocked must be true when generation_directive is blocked"
            )
        return self

    @model_validator(mode="after")
    def finalize_estimate_consistency(self) -> CoverageReport:
        estimates = self.qa_strategy_final.estimates
        if not estimates.preliminary:
            if estimates.estimated_new_test_cases != len(self.missing_scenarios):
                raise ValueError(
                    "estimated_new_test_cases must equal len(missing_scenarios) "
                    "when estimates are finalized"
                )
        return self
