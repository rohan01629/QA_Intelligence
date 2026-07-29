"""Preliminary coverage estimate heuristics (pre-inventory)."""

from __future__ import annotations

from qa_intelligence.domain.enums import RiskLevel, TestCategory
from qa_intelligence.domain.models.qa_strategy import CoverageEstimates
from qa_intelligence.domain.models.user_story import UserStory


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
    category_count = max(len(testing_required), 1)
    # Rough budget: ~1 scenario per AC per category group, scaled by risk.
    raw_new = ac_count * max(category_count // 2, 2)
    estimated_new = max(1, int(round(raw_new * _RISK_MULTIPLIER[risk])))
    # Without inventory we cannot know existing/duplicates; keep conservative placeholders.
    estimated_existing = 0
    estimated_duplicates = 0
    return CoverageEstimates(
        estimated_new_test_cases=estimated_new,
        estimated_existing_coverage=estimated_existing,
        estimated_duplicate_scenarios=estimated_duplicates,
        preliminary=True,
    )
