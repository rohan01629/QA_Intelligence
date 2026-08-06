"""Generation volume policy — Rule 11.

Fresh/simple stories: ~25 cases.
Large multi-scenario / high-risk stories: 50–60.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from qa_intelligence.domain.enums import GenerationDirective, RiskLevel
from qa_intelligence.domain.policies.product_rules import (
    MAX_GENERATED_TEST_CASES,
    MIN_GENERATED_TEST_CASES,
    TARGET_COMPLEX_TEST_CASES,
)

# Complexity thresholds (pre-expansion / story-native signals only).
_COMPLEX_AC_COUNT = 3
_COMPLEX_SCENARIO_MARKERS = 4
_COMPLEX_AC_CHARS = 1200
_COMPLEX_NATIVE_SCENARIOS = 8


@dataclass(frozen=True)
class StoryComplexity:
    """Whether a story should use the complex (50–60) generation band."""

    is_complex: bool
    reasons: tuple[str, ...] = ()


def assess_story_complexity(
    *,
    risk: RiskLevel | None = None,
    ac_count: int = 0,
    ac_texts: list[str] | None = None,
    native_scenario_count: int = 0,
) -> StoryComplexity:
    """Decide complexity from story-native signals — not from volume seed padding.

    Complex when any of:
    - risk is HIGH or CRITICAL
    - 3+ acceptance criteria items
    - 4+ explicit \"Scenario N:\" markers in AC text
    - combined AC text is long (>= 1200 chars)
    - 8+ native uncovered/AC scenarios before volume expansion
    """
    texts = [t for t in (ac_texts or []) if t and t.strip()]
    joined = "\n".join(texts)
    markers = len(re.findall(r"(?i)\bScenario\s+\d+\s*:", joined))
    reasons: list[str] = []

    if risk in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
        reasons.append(f"risk={risk.value if risk else 'unknown'}")
    if ac_count >= _COMPLEX_AC_COUNT:
        reasons.append(f"ac_count={ac_count}")
    if markers >= _COMPLEX_SCENARIO_MARKERS:
        reasons.append(f"scenario_markers={markers}")
    if len(joined) >= _COMPLEX_AC_CHARS:
        reasons.append(f"ac_chars={len(joined)}")
    if native_scenario_count >= _COMPLEX_NATIVE_SCENARIOS:
        reasons.append(f"native_scenarios={native_scenario_count}")

    return StoryComplexity(is_complex=bool(reasons), reasons=tuple(reasons))


def clamp_generation_budget(
    estimated: int,
    *,
    directive: GenerationDirective | None = None,
    risk: RiskLevel | None = None,
    scenario_count: int = 0,
    ac_count: int = 0,
    ac_texts: list[str] | None = None,
    existing_count: int = 0,
    is_complex: bool | None = None,
    min_cases: int = MIN_GENERATED_TEST_CASES,
    max_cases: int = MAX_GENERATED_TEST_CASES,
    complex_target: int = TARGET_COMPLEX_TEST_CASES,
) -> int:
    """Return a generation budget within configured volume bounds.

    - Fresh/simple: enforce ``min_cases`` (~25), do **not** jump to 50.
    - Fresh/complex: target ``complex_target`` (50), cap ``max_cases`` (60).
    - Gap-fill: respect missing work; do not force 50 on thin gaps.
    """
    raw = max(int(estimated), 0)
    is_fresh = (
        directive == GenerationDirective.FRESH_SUITE
        or existing_count == 0
    )

    if is_complex is None:
        is_complex = assess_story_complexity(
            risk=risk,
            ac_count=ac_count,
            ac_texts=ac_texts,
            native_scenario_count=scenario_count,
        ).is_complex

    if is_fresh:
        if is_complex:
            budget = max(raw, complex_target, min_cases)
        else:
            # Short/simple stories stay at the minimum band (~25).
            budget = min_cases
    else:
        if scenario_count >= min_cases:
            budget = max(raw, min_cases) if is_complex else max(raw, min(scenario_count, min_cases))
        else:
            budget = max(raw, scenario_count, 1)
            if scenario_count > 1:
                budget = max(budget, min(scenario_count * 3, min_cases))

    return max(1, min(budget, max_cases))
