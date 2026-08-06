"""Unit tests for Rule 11 generation volume policy."""

from __future__ import annotations

from qa_intelligence.domain.enums import GenerationDirective, RiskLevel
from qa_intelligence.domain.policies.generation_volume import (
    assess_story_complexity,
    clamp_generation_budget,
)
from qa_intelligence.domain.policies.product_rules import (
    MAX_GENERATED_TEST_CASES,
    MIN_GENERATED_TEST_CASES,
    TARGET_COMPLEX_TEST_CASES,
)


def test_fresh_suite_simple_stays_at_minimum_25() -> None:
    budget = clamp_generation_budget(
        1,
        directive=GenerationDirective.FRESH_SUITE,
        risk=RiskLevel.MEDIUM,
        scenario_count=1,
        ac_count=1,
        ac_texts=["Rename button and open dialog."],
        existing_count=0,
    )
    assert budget == MIN_GENERATED_TEST_CASES


def test_short_story_not_complex() -> None:
    complexity = assess_story_complexity(
        risk=RiskLevel.MEDIUM,
        ac_count=1,
        ac_texts=["Rename Download ASCII Report to ASCII Report."],
        native_scenario_count=1,
    )
    assert complexity.is_complex is False


def test_multi_scenario_story_is_complex() -> None:
    ac = "\n".join(f"Scenario {i}: do thing {i}" for i in range(1, 6))
    complexity = assess_story_complexity(
        risk=RiskLevel.MEDIUM,
        ac_count=1,
        ac_texts=[ac],
        native_scenario_count=1,
    )
    assert complexity.is_complex is True
    assert any("scenario_markers" in r for r in complexity.reasons)


def test_high_risk_targets_complex_volume() -> None:
    budget = clamp_generation_budget(
        5,
        directive=GenerationDirective.FRESH_SUITE,
        risk=RiskLevel.HIGH,
        scenario_count=2,
        ac_count=2,
        existing_count=0,
    )
    assert budget == TARGET_COMPLEX_TEST_CASES
    assert budget <= MAX_GENERATED_TEST_CASES


def test_many_ac_items_targets_complex_volume() -> None:
    budget = clamp_generation_budget(
        8,
        directive=GenerationDirective.FRESH_SUITE,
        risk=RiskLevel.MEDIUM,
        scenario_count=3,
        ac_count=3,
        ac_texts=["AC1", "AC2", "AC3"],
        existing_count=0,
    )
    assert budget >= TARGET_COMPLEX_TEST_CASES


def test_post_expansion_scenario_count_does_not_force_complex() -> None:
    """Padding/seeds must not flip a simple story to the 50 band."""
    budget = clamp_generation_budget(
        1,
        directive=GenerationDirective.FRESH_SUITE,
        risk=RiskLevel.LOW,
        scenario_count=40,  # would be wrong if used alone without is_complex
        ac_count=1,
        ac_texts=["Short rename story."],
        existing_count=0,
        is_complex=False,
    )
    assert budget == MIN_GENERATED_TEST_CASES


def test_never_exceeds_max() -> None:
    budget = clamp_generation_budget(
        200,
        directive=GenerationDirective.FRESH_SUITE,
        risk=RiskLevel.CRITICAL,
        scenario_count=100,
        existing_count=0,
    )
    assert budget == MAX_GENERATED_TEST_CASES
