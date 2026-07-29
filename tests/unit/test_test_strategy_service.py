"""Unit tests for TestStrategyService."""

from __future__ import annotations

from qa_intelligence.domain.enums import (
    FeatureType,
    GenerationDirective,
    RiskLevel,
    ScenarioDisposition,
    ScenarioSource,
    TestCategory,
)
from qa_intelligence.domain.models.analysis import FeatureAnalysis, RequirementAnalysis
from qa_intelligence.domain.models.coverage import CoverageReport, ScenarioRef
from qa_intelligence.domain.models.coverage_matrix import CoverageAnalysisResult
from qa_intelligence.domain.models.detection import DuplicateDetectionResult, ScenarioMatch
from qa_intelligence.domain.models.duplicate import DuplicateAnalysis
from qa_intelligence.domain.models.qa_strategy import (
    CategoryExclusion,
    CoverageEstimates,
    QAStrategy,
)
from qa_intelligence.services.test_strategy_service import TestStrategyService


def _requirement_analysis(*, blocked: bool = False) -> RequirementAnalysis:
    strategy = QAStrategy(
        feature_type=FeatureType.BACKEND_API,
        risk=RiskLevel.HIGH,
        testing_required=[
            TestCategory.POSITIVE,
            TestCategory.NEGATIVE,
            TestCategory.EDGE,
            TestCategory.VALIDATION,
            TestCategory.REGRESSION,
            TestCategory.API,
            TestCategory.INTEGRATION,
        ],
        testing_not_required=[
            CategoryExclusion(category=TestCategory.UI, reason="No UI changes"),
            CategoryExclusion(
                category=TestCategory.ACCESSIBILITY, reason="No UI changes"
            ),
            CategoryExclusion(
                category=TestCategory.DATABASE, reason="No database changes"
            ),
            CategoryExclusion(
                category=TestCategory.PERFORMANCE,
                reason="No performance requirements",
            ),
        ],
        reason=(
            "This user story modifies only backend API behavior "
            "without UI or database changes."
        ),
        estimates=CoverageEstimates(
            estimated_new_test_cases=0 if blocked else 10,
            preliminary=True,
        ),
        blocked=blocked,
    )
    return RequirementAnalysis(
        user_story_id=73230,
        feature_analysis=FeatureAnalysis(
            feature_type=FeatureType.BACKEND_API,
            risk_level=RiskLevel.HIGH,
            modules=["OrdersApi"],
            regression_impact="High regression risk for OrdersApi API changes.",
            applicable_optional_categories=[
                TestCategory.API,
                TestCategory.INTEGRATION,
            ],
            excluded_optional_categories=[
                TestCategory.UI,
                TestCategory.ACCESSIBILITY,
                TestCategory.DATABASE,
                TestCategory.PERFORMANCE,
            ],
            rationale="Backend API change",
        ),
        requirement_gaps=[],
        qa_strategy=strategy,
        blocked=blocked,
    )


def _coverage_report(missing: int = 4, covered: int = 2, bugs: int = 1) -> CoverageReport:
    base = _requirement_analysis().qa_strategy
    final = base.model_copy(
        update={
            "estimates": CoverageEstimates(
                estimated_new_test_cases=missing,
                estimated_existing_coverage=covered + bugs,
                estimated_duplicate_scenarios=0,
                preliminary=False,
            ),
            "blocked": False,
        }
    )
    return CoverageReport(
        user_story_id=73230,
        covered_scenarios=[
            ScenarioRef(key=f"c{i}", title=f"Covered {i}", source=ScenarioSource.EXISTING)
            for i in range(covered)
        ],
        bug_covered_scenarios=[
            ScenarioRef(key=f"b{i}", title=f"Bug {i}", source=ScenarioSource.BUG)
            for i in range(bugs)
        ],
        missing_scenarios=[
            ScenarioRef(key=f"m{i}", title=f"Missing {i}", source=ScenarioSource.MISSING)
            for i in range(missing)
        ],
        qa_strategy_final=final,
        generation_directive=GenerationDirective.GAP_FILL_ONLY,
    )


def test_builds_strategy_with_category_reasons_and_estimates() -> None:
    service = TestStrategyService()
    strategy = service.build_strategy(
        _requirement_analysis(),
        _coverage_report(missing=4, covered=2, bugs=1),
        DuplicateAnalysis(user_story_id=73230, duplicate_scenario_count=2),
    )

    assert strategy.feature_type == FeatureType.BACKEND_API
    assert strategy.risk_level == RiskLevel.HIGH
    assert strategy.blocked is False
    assert strategy.generation_directive == GenerationDirective.GAP_FILL_ONLY

    applicable = {d.category for d in strategy.applicable_categories}
    assert TestCategory.API in applicable
    assert TestCategory.INTEGRATION in applicable
    assert all(d.applicable and d.reason for d in strategy.applicable_categories)

    skipped = {d.category: d.reason for d in strategy.skipped_categories}
    assert TestCategory.UI in skipped
    assert "UI" in skipped[TestCategory.UI] or "ui" in skipped[TestCategory.UI].lower()

    # High risk multiplier on 4 uncovered ≈ 5–6
    assert strategy.estimated_new_test_cases >= 4
    assert strategy.estimated_existing_coverage == 3
    assert strategy.estimated_duplicate_scenarios == 2
    assert strategy.estimates.preliminary is False
    assert strategy.risk_based_strategy.focus_areas
    assert strategy.risk_based_strategy.priority_order
    assert "Backend API" in strategy.narrative_summary or "backend" in strategy.narrative_summary.lower()


def test_accepts_coverage_analysis_result_and_duplicate_detection_result() -> None:
    service = TestStrategyService()
    coverage = CoverageAnalysisResult(
        user_story_id=73230,
        uncovered_count=3,
        covered_by_test_count=1,
        covered_by_bug_count=1,
        uncovered_scenarios=[
            ScenarioRef(key="AC-2", title="Missing fields", source=ScenarioSource.MISSING)
        ],
    )
    duplicates = DuplicateDetectionResult(
        user_story_id=73230,
        duplicate=[
            ScenarioMatch(
                key="tc:2",
                title="Dup",
                disposition=ScenarioDisposition.DUPLICATE,
                similarity=0.9,
            )
        ],
        generate_new=[
            ScenarioMatch(
                key="AC-2",
                title="Missing fields",
                disposition=ScenarioDisposition.GENERATE_NEW,
            )
        ],
    )
    strategy = service.build_strategy(_requirement_analysis(), coverage, duplicates)
    assert strategy.estimated_new_test_cases >= 3
    assert strategy.estimated_existing_coverage == 2
    assert strategy.estimated_duplicate_scenarios >= 1


def test_blocked_requirements_zero_new_cases() -> None:
    req = _requirement_analysis(blocked=True)
    # CoverageReport validator requires matching blocked flags
    coverage = CoverageReport(
        user_story_id=73230,
        missing_scenarios=[],
        qa_strategy_final=req.qa_strategy.model_copy(
            update={
                "estimates": CoverageEstimates(
                    estimated_new_test_cases=0,
                    preliminary=False,
                ),
                "blocked": True,
            }
        ),
        generation_directive=GenerationDirective.BLOCKED,
    )
    strategy = TestStrategyService().build_strategy(
        req,
        coverage,
        DuplicateAnalysis(duplicate_scenario_count=0),
    )
    assert strategy.blocked is True
    assert strategy.estimated_new_test_cases == 0
    assert strategy.generation_directive == GenerationDirective.BLOCKED
