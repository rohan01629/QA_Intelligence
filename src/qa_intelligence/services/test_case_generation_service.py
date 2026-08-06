"""TestCaseGenerationService — generate only missing (or fresh-suite) test cases.

Enforces product rules:
  1 Never generate duplicates
  2 Fresh suite when no existing tests
  3 Only missing scenarios when existing tests exist
  5/6 Categories from analyzed strategy (core + applicable optional)
  7/8/9 Validated three-field cases with step/result parity
 10 Do not invent requirements when blocked / no AC — report gaps upstream
 12 Do not generate when US feature is absent from configured local codebases
 13 During generation, decide which TCs are Regression (~30%) vs Sanity (~10%),
     draft them for that role, then stamp ADO toggles from that decision
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
from qa_intelligence.domain.policies.category_mix import (
    MixSlotKind,
    classify_mix_for_records,
    plan_suite_mix,
    stamp_mix_flags_on_case,
)
from qa_intelligence.domain.policies.product_rules import CORE_CATEGORIES_ORDERED
from qa_intelligence.domain.policies.generation_volume import (
    assess_story_complexity,
    clamp_generation_budget,
)
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
        implementation_summary: object | None = None,
        allow_related_implementation: bool = False,
    ) -> TestCaseGenerationResult:
        """Generate ONLY missing scenarios, or a fresh suite when none exist.

        ``implementation_summary`` is optional. When provided, validation rules and
        regression areas enrich scenario targets. When omitted, behavior is unchanged.

        Rule 12: if ``feature_found`` is False, generation is blocked unless
        ``allow_related_implementation`` is True (user approved related/legacy drafts).
        """
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

        # Rule 12: US feature missing — optional related-implementation path.
        if implementation_summary is not None and getattr(
            implementation_summary, "feature_found", True
        ) is False and not allow_related_implementation:
            related_available = bool(
                getattr(
                    implementation_summary,
                    "related_implementation_available",
                    False,
                )
            )
            return TestCaseGenerationResult(
                user_story_id=user_story.id,
                mode=GenerationMode.BLOCKED,
                generation_directive=GenerationDirective.BLOCKED,
                blocked=True,
                notes=(
                    "Generation paused (Rule 12): User Story feature is not implemented. "
                    + (
                        "Related/previous implementation was found — ask the user whether "
                        "to generate TCs from that related code "
                        "(allow_related_implementation=true). "
                        if related_available
                        else "No related implementation found; generation skipped. "
                    )
                    + f"{getattr(implementation_summary, 'feature_presence_notes', '')}"
                ).strip(),
            )

        # Rules 2 & 3: inventory presence drives mode (absolute).
        mode, scenarios = self._resolve_targets(
            user_story=user_story,
            criteria=criteria,
            existing=existing,
            uncovered_scenarios=uncovered_scenarios,
        )
        # Assess complexity from story-native signals BEFORE enrichment/seeding.
        complexity = assess_story_complexity(
            risk=test_strategy.risk_level,
            ac_count=len(criteria),
            ac_texts=ac_texts,
            native_scenario_count=len(scenarios),
        )
        scenarios = self._enrich_scenarios_from_implementation(
            scenarios,
            implementation_summary,
            mode=mode,
        )
        scenarios = self._expand_scenarios_for_volume(
            scenarios,
            user_story=user_story,
            mode=mode,
            is_complex=complexity.is_complex,
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
        budget = clamp_generation_budget(
            test_strategy.estimated_new_test_cases,
            directive=(
                GenerationDirective.FRESH_SUITE
                if mode == GenerationMode.FRESH_SUITE
                else GenerationDirective.GAP_FILL_ONLY
            ),
            risk=test_strategy.risk_level,
            scenario_count=len(criteria) or 1,
            ac_count=len(criteria),
            ac_texts=ac_texts,
            existing_count=len(existing),
            is_complex=complexity.is_complex,
        )
        if budget <= 0:
            budget = max(len(scenarios), 1)

        generated: list[TestCase] = []
        records: list[GeneratedTestCaseRecord] = []
        rejected_count = 0

        category_cycle = categories or list(CORE_CATEGORIES_ORDERED)
        # Rule 13: decide Regression vs Sanity roles first, then generate for that role.
        plan, planned_mix = plan_suite_mix(budget, scenarios, category_cycle)
        max_attempts = max(len(plan) * 3, budget * 3)
        plan_index = 0
        fill_index = 0

        while len(generated) < budget and scenarios and (plan_index < max_attempts):
            if plan_index < len(plan):
                item = plan[plan_index]
                scenario = item.scenario
                category = item.category
                mix_kind = item.mix_kind
            else:
                # Fallback fill if duplicates rejected planned slots.
                scenario = scenarios[fill_index % len(scenarios)]
                category = category_cycle[fill_index % len(category_cycle)]
                mix_kind = MixSlotKind.STANDARD
                fill_index += 1
            plan_index += 1

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
                        mix_kind=MixSlotKind.STANDARD.value,
                        is_critical=False,
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
                        mix_kind=MixSlotKind.STANDARD.value,
                        is_critical=False,
                    )
                )
                continue

            # Stamp ADO mix flags from the generation-time Rule 13 decision.
            case = stamp_mix_flags_on_case(case, mix_kind.value)
            generated.append(case)
            records.append(
                GeneratedTestCaseRecord(
                    source_scenario_key=scenario.key,
                    category=category,
                    test_case=case,
                    validation=validation,
                    rejected=False,
                    mix_kind=mix_kind.value,
                    is_critical=mix_kind == MixSlotKind.CRITICAL,
                )
            )

        # Finalize stamps / recount from generation decisions (no role reassignment).
        records, mix, regression_ids, critical_ids = classify_mix_for_records(records)
        generated = [
            r.test_case
            for r in records
            if not r.rejected and r.test_case is not None
        ]

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
                f"in {mode.value} mode; rejected {rejected_count}. "
                f"Rule 13 planned regression={planned_mix.regression}/"
                f"sanity={planned_mix.critical}; "
                f"marked regression={mix.regression_selected}/"
                f"sanity={mix.critical_selected}. "
                f"Regression TC#s: {regression_ids or 'none'}; "
                f"Critical/Sanity TC#s: {critical_ids or 'none'} "
                "(roles decided during generation, then ADO toggles applied)."
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

    def _enrich_scenarios_from_implementation(
        self,
        scenarios: list[ScenarioRef],
        implementation_summary: object | None,
        *,
        mode: GenerationMode,
    ) -> list[ScenarioRef]:
        """Append implementation-derived missing intents without dropping AC scenarios.

        Only used when an ImplementationSummary is supplied. No-op when None.
        """
        if implementation_summary is None:
            return scenarios

        # Duck-typed to avoid hard import cycles in optional path; validate attrs.
        validation_rules = list(getattr(implementation_summary, "validation_rules", []) or [])
        regression_areas = list(getattr(implementation_summary, "regression_areas", []) or [])
        affected_apis = list(getattr(implementation_summary, "affected_apis", []) or [])

        extras: list[ScenarioRef] = []
        existing_titles = {s.title.strip().lower() for s in scenarios}

        for index, rule in enumerate(validation_rules, start=1):
            title = rule.strip()
            if not title or title.lower() in existing_titles:
                continue
            extras.append(
                ScenarioRef(
                    key=f"CODE-VAL-{index}",
                    title=title,
                    source=ScenarioSource.MISSING,
                )
            )
            existing_titles.add(title.lower())

        for index, api in enumerate(affected_apis, start=1):
            method = getattr(api, "method", "") or ""
            path = getattr(api, "path", "") or ""
            title = f"API {method} {path}".strip()
            if not path or title.lower() in existing_titles:
                continue
            extras.append(
                ScenarioRef(
                    key=f"CODE-API-{index}",
                    title=title,
                    source=ScenarioSource.MISSING,
                )
            )
            existing_titles.add(title.lower())

        for index, area in enumerate(regression_areas, start=1):
            title = f"Regression: {area}".strip()
            if not area or title.lower() in existing_titles:
                continue
            # In gap-fill mode, only add regression if we already have some missing work.
            if mode == GenerationMode.GAP_FILL_ONLY and not scenarios and not extras:
                break
            extras.append(
                ScenarioRef(
                    key=f"CODE-REG-{index}",
                    title=title,
                    source=ScenarioSource.MISSING,
                )
            )
            existing_titles.add(title.lower())

        return [*scenarios, *extras]

    def _expand_scenarios_for_volume(
        self,
        scenarios: list[ScenarioRef],
        *,
        user_story: UserStory,
        mode: GenerationMode,
        is_complex: bool = False,
    ) -> list[ScenarioRef]:
        """Decompose coarse AC blobs into atomic intents so Rule 11 volume can be met.

        Simple stories get a modest seed set (~25 band). Complex stories get a
        larger seed set to support the 50–60 band.
        """
        import re

        expanded: list[ScenarioRef] = []
        seen: set[str] = set()

        def _add(key: str, title: str) -> None:
            cleaned = " ".join(title.split()).strip()
            if len(cleaned) < 8:
                return
            low = cleaned.lower()
            if low in seen:
                return
            seen.add(low)
            expanded.append(
                ScenarioRef(key=key, title=cleaned[:240], source=ScenarioSource.MISSING)
            )

        for scenario in scenarios:
            _add(scenario.key, scenario.title)
            parts = re.split(
                r"(?i)\bScenario\s+\d+\s*:|\bGiven\b|\bWhen\b|\bThen\b|\.(?=\s+[A-Z])",
                scenario.title,
            )
            for index, part in enumerate(parts, start=1):
                chunk = part.strip(" :-")
                if chunk:
                    _add(f"{scenario.key}-P{index}", chunk)

        if mode == GenerationMode.FRESH_SUITE:
            feature = user_story.title.strip() or "feature"
            simple_seeds = [
                f"Positive path for {feature}",
                f"Negative path / rejection for {feature}",
                f"Edge case for {feature}",
                f"Validation rules for {feature}",
                f"Regression safety for adjacent screens after {feature}",
                f"UI label and control visibility for {feature}",
                f"Cancel / dismiss without save for {feature}",
                f"Operator / permission guard for {feature}",
                f"Error handling / failure path for {feature}",
                f"Dialog / modal open behavior for {feature}",
                f"Dialog primary action for {feature}",
                f"Dialog Cancel action for {feature}",
                f"Dialog close discards unsaved changes for {feature}",
                f"Default selection / load behavior for {feature}",
                f"User can modify selections for {feature}",
                f"API load on open for {feature}",
                f"API failure handling on open for {feature}",
                f"Empty inventory / empty state for {feature}",
                f"Re-open after cancel shows clean defaults for {feature}",
                f"Neighbor controls remain unchanged for {feature}",
            ]
            complex_extra = [
                f"No premature command invocation for {feature}",
                f"Configuration retained only after explicit confirm for {feature}",
                f"Tooltip / i18n label update for {feature}",
                f"Disabled state when prerequisite connection missing for {feature}",
                f"Concurrent click / double-click protection for {feature}",
                f"Persist / refresh behavior after completing {feature}",
                f"Keyboard / accessibility basic open-close for {feature}",
                f"Success feedback after confirm for {feature}",
                f"Failure feedback after confirm for {feature}",
                f"Partial selection persistence across tabs for {feature}",
                f"Select-all / clear-all header behavior for {feature}",
                f"Unknown ids in saved selection ignored safely for {feature}",
                f"Multi-tab state isolation for {feature}",
                f"Large channel list performance sanity for {feature}",
                f"Mixed default rules across tabs for {feature}",
            ]
            seeds = simple_seeds + (complex_extra if is_complex else [])
            for index, seed in enumerate(seeds, start=1):
                _add(f"VOL-{index}", seed)

        return expanded or scenarios
