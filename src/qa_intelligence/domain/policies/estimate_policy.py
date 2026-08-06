"""Preliminary coverage estimate heuristics (pre-inventory)."""

from __future__ import annotations

from qa_intelligence.domain.enums import GenerationDirective, RiskLevel, TestCategory
from qa_intelligence.domain.models.qa_strategy import CoverageEstimates
from qa_intelligence.domain.models.user_story import UserStory
from qa_intelligence.domain.policies.generation_volume import clamp_generation_budget


_RISK_MULTIPLIER = {
    RiskLevel.LOW: 0.8,
    RiskLevel.MEDIUM: 1.0,
    RiskLevel.HIGH: 1.3,
    RiskLevel.CRITICAL: 1.6,
}


def preliminary_estimates(
    story: UserStory,
    testing_required: list[TestCategory],
    risk: RiskLevel,
    *,
    blocked: bool,
) -> CoverageEstimates:
    if blocked:
        return CoverageEstimates(
            estimated_new_test_cases=0,
            estimated_existing_coverage=0,
            estimated_duplicate_scenarios=0,
            preliminary=True,
        )

    ac_count = max(len(story.acceptance_criteria), 1)
    ac_texts = [ac.text for ac in story.acceptance_criteria]
    category_count = max(len(testing_required), 1)
    raw_new = ac_count * max(category_count // 2, 2)
    estimated_new = max(1, int(round(raw_new * _RISK_MULTIPLIER[risk])))
    estimated_new = clamp_generation_budget(
        estimated_new,
        directive=GenerationDirective.FRESH_SUITE,
        risk=risk,
        scenario_count=ac_count,
        ac_count=ac_count,
        ac_texts=ac_texts,
        existing_count=0,
    )
    return CoverageEstimates(
        estimated_new_test_cases=estimated_new,
        estimated_existing_coverage=0,
        estimated_duplicate_scenarios=0,
        preliminary=True,
    )
