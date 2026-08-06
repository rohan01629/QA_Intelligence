"""TestStrategyService — synthesize risk-based QA strategy from analyses.

Inputs: RequirementAnalysis, Coverage Report/Result, Duplicate Analysis/Result.
Output: applicable/skipped categories with reasons, estimates, risk-based plan.

Does NOT generate test cases.
"""

from __future__ import annotations

import structlog

from qa_intelligence.domain.enums import (
    ALWAYS_TEST_CATEGORIES,
    GenerationDirective,
    RiskLevel,
    TestCategory,
)
from qa_intelligence.domain.models.analysis import RequirementAnalysis
from qa_intelligence.domain.models.coverage import CoverageReport
from qa_intelligence.domain.models.coverage_matrix import CoverageAnalysisResult
from qa_intelligence.domain.models.detection import DuplicateDetectionResult
from qa_intelligence.domain.models.duplicate import DuplicateAnalysis
from qa_intelligence.domain.models.qa_strategy import (
    CategoryExclusion,
    CoverageEstimates,
    QAStrategy,
)
from qa_intelligence.domain.models.test_strategy import (
    CategoryDecision,
    RiskBasedTestingStrategy,
    TestStrategy,
)

from qa_intelligence.domain.policies.generation_volume import clamp_generation_budget

logger = structlog.get_logger(__name__)

_RISK_CASE_MULTIPLIER: dict[RiskLevel, float] = {
    RiskLevel.LOW: 0.8,
    RiskLevel.MEDIUM: 1.0,
    RiskLevel.HIGH: 1.35,
    RiskLevel.CRITICAL: 1.7,
}

_ALWAYS_REASONS: dict[TestCategory, str] = {
    TestCategory.POSITIVE: "Always-on: confirm happy-path behavior for the change",
    TestCategory.NEGATIVE: "Always-on: confirm rejection/failure paths",
    TestCategory.EDGE: "Always-on: cover boundary and unusual inputs",
    TestCategory.VALIDATION: "Always-on: verify stated validation rules",
    TestCategory.REGRESSION: "Always-on: protect adjacent behavior from regressions",
}


class TestStrategyService:
    """Build a testing strategy from requirement, coverage, and duplicate inputs."""

    def build_strategy(
        self,
        requirement_analysis: RequirementAnalysis,
        coverage_report: CoverageReport | CoverageAnalysisResult,
        duplicate_analysis: DuplicateAnalysis | DuplicateDetectionResult,
    ) -> TestStrategy:
        """Create the strategy only — no test case generation."""
        base = requirement_analysis.qa_strategy
        risk = base.risk
        feature_type = base.feature_type
        blocked = requirement_analysis.blocked or base.blocked

        uncovered_count, covered_count, bug_covered_count = _coverage_counts(
            coverage_report
        )
        duplicate_count = _duplicate_count(duplicate_analysis)

        applicable = self._applicable_decisions(base, risk)
        skipped = self._skipped_decisions(base)

        cases_per_gap = _RISK_CASE_MULTIPLIER[risk]
        if blocked:
            estimated_new = 0
            directive = GenerationDirective.BLOCKED
        else:
            # Prefer uncovered requirement count; fall back to generate_new from duplicates.
            gap_basis = uncovered_count
            if gap_basis == 0 and isinstance(
                duplicate_analysis, DuplicateDetectionResult
            ):
                gap_basis = len(duplicate_analysis.generate_new)
            estimated_new = int(round(gap_basis * cases_per_gap))
            if gap_basis > 0 and estimated_new == 0:
                estimated_new = gap_basis
            if covered_count == 0 and bug_covered_count == 0 and uncovered_count > 0:
                directive = GenerationDirective.FRESH_SUITE
            elif blocked:
                directive = GenerationDirective.BLOCKED
            else:
                directive = GenerationDirective.GAP_FILL_ONLY

            ac_count, ac_texts = _acceptance_signals(coverage_report)
            estimated_new = clamp_generation_budget(
                estimated_new,
                directive=directive,
                risk=risk,
                scenario_count=max(uncovered_count, gap_basis),
                ac_count=ac_count,
                ac_texts=ac_texts,
                existing_count=covered_count,
            )

        estimated_existing = covered_count + bug_covered_count
        estimates = CoverageEstimates(
            estimated_new_test_cases=estimated_new,
            estimated_existing_coverage=estimated_existing,
            estimated_duplicate_scenarios=duplicate_count,
            preliminary=False,
        )

        risk_plan = self._risk_based_plan(
            risk=risk,
            applicable=[d.category for d in applicable],
            feature_type_label=feature_type.display_name,
            regression_impact=requirement_analysis.feature_analysis.regression_impact,
            cases_per_gap=cases_per_gap,
        )

        qa_strategy = QAStrategy(
            feature_type=feature_type,
            risk=risk,
            testing_required=[d.category for d in applicable],
            testing_not_required=[
                CategoryExclusion(category=d.category, reason=d.reason)
                for d in skipped
            ],
            reason=base.reason,
            estimates=estimates,
            blocked=blocked,
        )

        narrative = _narrative_summary(
            feature_type=feature_type.display_name,
            risk=risk,
            applicable=applicable,
            skipped=skipped,
            estimated_new=estimated_new,
            estimated_existing=estimated_existing,
            duplicate_count=duplicate_count,
            blocked=blocked,
            directive=directive,
        )

        strategy = TestStrategy(
            user_story_id=requirement_analysis.user_story_id,
            feature_type=feature_type,
            risk_level=risk,
            applicable_categories=applicable,
            skipped_categories=skipped,
            estimated_new_test_cases=estimated_new,
            estimated_existing_coverage=estimated_existing,
            estimated_duplicate_scenarios=duplicate_count,
            risk_based_strategy=risk_plan,
            narrative_summary=narrative,
            blocked=blocked,
            generation_directive=directive,
            estimates=estimates,
            qa_strategy=qa_strategy,
        )

        logger.info(
            "test_strategy.built",
            user_story_id=strategy.user_story_id,
            risk=risk.value,
            applicable=len(applicable),
            skipped=len(skipped),
            estimated_new=estimated_new,
            blocked=blocked,
            directive=directive.value,
        )
        return strategy

    def _applicable_decisions(
        self,
        base: QAStrategy,
        risk: RiskLevel,
    ) -> list[CategoryDecision]:
        decisions: list[CategoryDecision] = []
        for category in base.testing_required:
            if category in ALWAYS_TEST_CATEGORIES:
                reason = _ALWAYS_REASONS.get(
                    category,
                    f"Always-on category for {base.feature_type.display_name}",
                )
            else:
                reason = (
                    f"Applicable for {base.feature_type.display_name}: "
                    f"requirement signals justify {category.display_name} testing"
                )
            priority = _category_priority(category, risk)
            decisions.append(
                CategoryDecision(
                    category=category,
                    applicable=True,
                    reason=reason,
                    priority=priority,
                )
            )
        return decisions

    def _skipped_decisions(self, base: QAStrategy) -> list[CategoryDecision]:
        return [
            CategoryDecision(
                category=item.category,
                applicable=False,
                reason=item.reason,
                priority=RiskLevel.LOW,
            )
            for item in base.testing_not_required
        ]

    def _risk_based_plan(
        self,
        *,
        risk: RiskLevel,
        applicable: list[TestCategory],
        feature_type_label: str,
        regression_impact: str | None,
        cases_per_gap: float,
    ) -> RiskBasedTestingStrategy:
        focus = _focus_areas(risk, applicable)
        depth = _depth_guidance(risk, cases_per_gap)
        regression = regression_impact or (
            f"{risk.display_name} regression emphasis for {feature_type_label} changes."
        )
        priority_order = _priority_order(applicable, risk)
        return RiskBasedTestingStrategy(
            risk_level=risk,
            focus_areas=focus,
            depth_guidance=depth,
            regression_emphasis=regression,
            priority_order=priority_order,
            recommended_cases_per_uncovered_scenario=cases_per_gap,
        )


def _coverage_counts(
    coverage: CoverageReport | CoverageAnalysisResult,
) -> tuple[int, int, int]:
    """Return (uncovered, covered_by_test, covered_by_bug)."""
    if isinstance(coverage, CoverageAnalysisResult):
        return (
            coverage.uncovered_count,
            coverage.covered_by_test_count,
            coverage.covered_by_bug_count,
        )
    return (
        len(coverage.missing_scenarios),
        len(coverage.covered_scenarios),
        len(coverage.bug_covered_scenarios),
    )


def _acceptance_signals(
    coverage: CoverageReport | CoverageAnalysisResult,
) -> tuple[int, list[str]]:
    """Story-native AC count/text for Rule 11 complexity (not gap padding)."""
    if isinstance(coverage, CoverageAnalysisResult) and coverage.acceptance_criteria:
        texts = [ac.text for ac in coverage.acceptance_criteria]
        return len(texts), texts
    if isinstance(coverage, CoverageReport):
        texts = [s.title for s in coverage.missing_scenarios[:20] if s.title]
        return max(len(coverage.missing_scenarios), 1), texts
    return 1, []


def _duplicate_count(
    duplicate_analysis: DuplicateAnalysis | DuplicateDetectionResult,
) -> int:
    if isinstance(duplicate_analysis, DuplicateDetectionResult):
        clustered = sum(len(c.duplicates) for c in duplicate_analysis.clusters)
        return max(clustered, len(duplicate_analysis.duplicate))
    return duplicate_analysis.duplicate_scenario_count


def _category_priority(category: TestCategory, risk: RiskLevel) -> RiskLevel:
    if risk in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
        if category in {
            TestCategory.NEGATIVE,
            TestCategory.VALIDATION,
            TestCategory.SECURITY,
            TestCategory.PERMISSION,
            TestCategory.EDGE,
        }:
            return risk
    if category in ALWAYS_TEST_CATEGORIES:
        return RiskLevel.MEDIUM if risk == RiskLevel.LOW else risk
    return RiskLevel.MEDIUM


def _focus_areas(risk: RiskLevel, applicable: list[TestCategory]) -> list[str]:
    areas: list[str] = []
    if risk in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
        areas.extend(
            [
                "Prioritize negative, validation, and edge coverage for uncovered AC",
                "Strengthen regression around impacted modules",
            ]
        )
        if TestCategory.SECURITY in applicable:
            areas.append("Include security checks where signals exist")
        if TestCategory.API in applicable:
            areas.append("Exercise API contract and status-code paths thoroughly")
    elif risk == RiskLevel.MEDIUM:
        areas.append("Balance positive paths with representative negative/edge cases")
    else:
        areas.append("Keep suite lean: core positive and validation only where needed")
    return areas


def _depth_guidance(risk: RiskLevel, cases_per_gap: float) -> str:
    return (
        f"Risk={risk.display_name}: target about {cases_per_gap:.2f} test cases "
        f"per uncovered requirement scenario across applicable categories."
    )


def _priority_order(
    applicable: list[TestCategory],
    risk: RiskLevel,
) -> list[TestCategory]:
    high_first = (
        TestCategory.NEGATIVE,
        TestCategory.VALIDATION,
        TestCategory.EDGE,
        TestCategory.SECURITY,
        TestCategory.PERMISSION,
        TestCategory.API,
        TestCategory.INTEGRATION,
        TestCategory.POSITIVE,
        TestCategory.REGRESSION,
    )
    if risk in {RiskLevel.LOW, RiskLevel.MEDIUM}:
        high_first = (
            TestCategory.POSITIVE,
            TestCategory.VALIDATION,
            TestCategory.NEGATIVE,
            TestCategory.EDGE,
            TestCategory.REGRESSION,
            TestCategory.API,
            TestCategory.INTEGRATION,
        )
    ordered = [c for c in high_first if c in applicable]
    ordered.extend([c for c in applicable if c not in ordered])
    return ordered


def _narrative_summary(
    *,
    feature_type: str,
    risk: RiskLevel,
    applicable: list[CategoryDecision],
    skipped: list[CategoryDecision],
    estimated_new: int,
    estimated_existing: int,
    duplicate_count: int,
    blocked: bool,
    directive: GenerationDirective,
) -> str:
    if blocked:
        return (
            f"Testing strategy blocked for {feature_type} ({risk.display_name} risk) "
            "due to incomplete requirements. Resolve gaps before generating tests."
        )
    applicable_names = ", ".join(d.category.display_name for d in applicable)
    skipped_names = ", ".join(d.category.display_name for d in skipped) or "none"
    return (
        f"{feature_type} / {risk.display_name} risk. "
        f"Applicable: {applicable_names}. Skipped: {skipped_names}. "
        f"Estimate {estimated_new} new test case(s); "
        f"{estimated_existing} already covered; "
        f"{duplicate_count} duplicate scenario(s). "
        f"Directive: {directive.value}."
    )
