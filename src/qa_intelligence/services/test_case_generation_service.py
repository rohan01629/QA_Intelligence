"""TestCaseGenerationService — generate only missing (or fresh-suite) test cases.

Enforces product rules:
  1 Never generate duplicates
  2 Fresh suite when no existing tests
  3 Only missing scenarios when existing tests exist
  5/6 Categories from analyzed strategy (core + applicable optional)
  7/8/9 Validated three-field cases with step/result parity
 10 Do not invent requirements when blocked / no AC — report gaps upstream
"""

from __future__ import annotations

import structlog

from qa_intelligence.domain.enums import GenerationDirective, ScenarioSource, TestCategory
from qa_intelligence.domain.models.coverage import ScenarioRef
from qa_intelligence.domain.models.generation import (
    GeneratedTestCaseRecord,
    GenerationMode,
    TestCaseGenerationResult,
)
from qa_intelligence.domain.models.read_models import TestCaseSummary
from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.domain.models.test_strategy import TestStrategy
from qa_intelligence.domain.models.user_story import AcceptanceCriteria, UserStory
from qa_intelligence.domain.models.validation import ValidationIssue, ValidationResult
from qa_intelligence.domain.policies.product_rules import CORE_CATEGORIES_ORDERED
from qa_intelligence.domain.validation.duplicate_guard import is_duplicate_of_existing
from qa_intelligence.domain.validation.test_case_validator import validate_test_case_payload
from qa_intelligence.services.generation_templates import build_draft_for_category

logger = structlog.get_logger(__name__)


class TestCaseGenerationService:
    """Generate validated TestCase drafts from strategy + uncovered intents."""

    def generate(
        self,
        test_strategy: TestStrategy,
        user_story: UserStory,
        acceptance_criteria: list[AcceptanceCriteria] | None = None,
        *,
        existing_test_cases: list[TestCaseSummary] | None = None,
        uncovered_scenarios: list[ScenarioRef] | None = None,
    ) -> TestCaseGenerationResult:
        """Generate ONLY missing scenarios, or a fresh suite when none exist."""
        criteria = acceptance_criteria if acceptance_criteria is not None else list(
            user_story.acceptance_criteria
        )
        existing = existing_test_cases or []
        ac_texts = [ac.text for ac in criteria]

        # Rule 10: blocked / incomplete requirements → do not invent cases.
        if test_strategy.blocked or test_strategy.generation_directive == GenerationDirective.BLOCKED:
            return TestCaseGenerationResult(
                user_story_id=user_story.id,
                mode=GenerationMode.BLOCKED,
                generation_directive=GenerationDirective.BLOCKED,
                blocked=True,
                notes=(
                    "Generation blocked by incomplete requirements. "
                    "Requirement gaps must be reported; do not infer missing AC."
                ),
            )

        # Rules 2 & 3: inventory presence drives mode (absolute).
        mode, scenarios = self._resolve_targets(
            user_story=user_story,
            criteria=criteria,
            existing=existing,
            uncovered_scenarios=uncovered_scenarios,
        )

        if not scenarios:
            return TestCaseGenerationResult(
                user_story_id=user_story.id,
                mode=mode,
                generation_directive=(
                    GenerationDirective.FRESH_SUITE
                    if mode == GenerationMode.FRESH_SUITE
                    else GenerationDirective.GAP_FILL_ONLY
                ),
                notes="No missing scenarios to generate.",
            )

        # Rules 4–6: categories come from analyzed strategy (core + applicable optional).
        categories = self._categories_for_generation(test_strategy)
        budget = test_strategy.estimated_new_test_cases
        if budget <= 0:
            budget = max(len(scenarios), 1)

        generated: list[TestCase] = []
        records: list[GeneratedTestCaseRecord] = []
        rejected_count = 0

        category_cycle = categories or list(CORE_CATEGORIES_ORDERED)
        index = 0
        max_attempts = budget * max(len(category_cycle), 1) * 3

        while len(generated) < budget and scenarios and index < max_attempts:
            scenario = scenarios[index % len(scenarios)]
            category = category_cycle[index % len(category_cycle)]
            index += 1

            draft = build_draft_for_category(
                scenario_title=scenario.title,
                category=category,
                feature_type=test_strategy.feature_type,
                story_title=user_story.title,
            )
            # Rules 7–9: hard validation (parity + three fields only).
            case, validation = validate_test_case_payload(draft)
            if case is None or not validation.is_valid:
                rejected_count += 1
                records.append(
                    GeneratedTestCaseRecord(
                        source_scenario_key=scenario.key,
                        category=category,
                        test_case=None,
                        validation=validation,
                        rejected=True,
                    )
                )
                continue

            # Rule 1: never generate duplicates vs existing inventory or this batch.
            is_dup, score, matched = is_duplicate_of_existing(
                case,
                [*existing, *generated],
                ac_texts=ac_texts,
            )
            if is_dup:
                rejected_count += 1
                records.append(
                    GeneratedTestCaseRecord(
                        source_scenario_key=scenario.key,
                        category=category,
                        test_case=None,
                        validation=ValidationResult.failure(
                            [
                                ValidationIssue(
                                    code="DUPLICATE_TEST_CASE",
                                    message=(
                                        f"Duplicate of existing/generated case "
                                        f"'{matched}' (similarity={score:.2f})"
                                    ),
                                    field="title",
                                    details={
                                        "matched": matched,
                                        "similarity": score,
                                    },
                                )
                            ]
                        ),
                        rejected=True,
                    )
                )
                continue

            generated.append(case)
            records.append(
                GeneratedTestCaseRecord(
                    source_scenario_key=scenario.key,
                    category=category,
                    test_case=case,
                    validation=validation,
                    rejected=False,
                )
            )

        directive = (
            GenerationDirective.FRESH_SUITE
            if mode == GenerationMode.FRESH_SUITE
            else GenerationDirective.GAP_FILL_ONLY
        )
        result = TestCaseGenerationResult(
            user_story_id=user_story.id,
            mode=mode,
            generation_directive=directive,
            generated=generated,
            records=records,
            rejected_count=rejected_count,
            notes=(
                f"Generated {len(generated)} validated test case(s) "
                f"in {mode.value} mode; rejected {rejected_count}."
            ),
        )
        logger.info(
            "test_case.generation_completed",
            user_story_id=user_story.id,
            mode=mode.value,
            generated=len(generated),
            rejected=rejected_count,
            budget=budget,
        )
        return result

    def _resolve_targets(
        self,
        *,
        user_story: UserStory,
        criteria: list[AcceptanceCriteria],
        existing: list[TestCaseSummary],
        uncovered_scenarios: list[ScenarioRef] | None,
    ) -> tuple[GenerationMode, list[ScenarioRef]]:
        # Rule 2: no inventory → fresh suite from AC / uncovered.
        if not existing:
            mode = GenerationMode.FRESH_SUITE
            if uncovered_scenarios:
                return mode, list(uncovered_scenarios)
            if criteria:
                return mode, [
                    ScenarioRef(
                        key=ac.id or f"AC-{ac.order}",
                        title=ac.text,
                        source=ScenarioSource.MISSING,
                    )
                    for ac in criteria
                ]
            # Rule 10: no AC and no uncovered → do not invent scenarios.
            return mode, []

        # Rule 3: inventory present → only missing / uncovered scenarios.
        mode = GenerationMode.GAP_FILL_ONLY
        if uncovered_scenarios:
            return mode, list(uncovered_scenarios)
        return mode, []

    def _categories_for_generation(self, strategy: TestStrategy) -> list[TestCategory]:
        """Use analyzed strategy categories only (Rules 4–6)."""
        ordered = list(strategy.risk_based_strategy.priority_order)
        if not ordered:
            ordered = [d.category for d in strategy.applicable_categories if d.applicable]

        # Denied categories must never appear.
        denied = {
            d.category
            for d in strategy.skipped_categories
            if not d.applicable
        }
        # Also honor QA strategy exclusions when present.
        if strategy.qa_strategy is not None:
            denied.update(ex.category for ex in strategy.qa_strategy.testing_not_required)

        seen: set[TestCategory] = set()
        unique: list[TestCategory] = []
        for category in ordered:
            if category in denied or category in seen:
                continue
            seen.add(category)
            unique.append(category)

        # Ensure core categories remain first when applicable.
        cores = [c for c in CORE_CATEGORIES_ORDERED if c in seen]
        optionals = [c for c in unique if c not in CORE_CATEGORIES_ORDERED]
        return cores + optionals if cores or optionals else list(CORE_CATEGORIES_ORDERED)
