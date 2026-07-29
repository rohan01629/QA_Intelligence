"""Unit tests for analysis and coverage domain models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from qa_intelligence.domain.enums import (
    DuplicateBasis,
    FeatureType,
    GapSeverity,
    GenerationDirective,
    RequirementGapType,
    RiskLevel,
    ScenarioSource,
    TestCategory,
)
from qa_intelligence.domain.models import (
    AcceptanceCriteria,
    Bug,
    CategoryExclusion,
    CoverageEstimates,
    CoverageReport,
    DuplicateAnalysis,
    DuplicateCluster,
    FeatureAnalysis,
    QAStrategy,
    RequirementAnalysis,
    RequirementGap,
    ScenarioRef,
    UserStory,
    ValidationIssue,
    ValidationResult,
)


def _strategy(**overrides: object) -> QAStrategy:
    data: dict[str, object] = {
        "feature_type": FeatureType.BACKEND_API,
        "risk": RiskLevel.HIGH,
        "testing_required": [
            TestCategory.POSITIVE,
            TestCategory.NEGATIVE,
            TestCategory.EDGE,
            TestCategory.VALIDATION,
            TestCategory.REGRESSION,
            TestCategory.API,
            TestCategory.INTEGRATION,
        ],
        "testing_not_required": [
            CategoryExclusion(category=TestCategory.UI, reason="No UI changes"),
            CategoryExclusion(
                category=TestCategory.ACCESSIBILITY, reason="No UI changes"
            ),
            CategoryExclusion(
                category=TestCategory.DATABASE, reason="No database changes"
            ),
            CategoryExclusion(
                category=TestCategory.PERFORMANCE, reason="No performance requirements"
            ),
        ],
        "reason": (
            "This user story modifies only backend API behavior "
            "without UI or database changes."
        ),
        "estimates": CoverageEstimates(
            estimated_new_test_cases=18,
            estimated_existing_coverage=32,
            estimated_duplicate_scenarios=14,
            preliminary=False,
        ),
        "blocked": False,
    }
    data.update(overrides)
    return QAStrategy.model_validate(data)


def test_user_story_with_acceptance_criteria() -> None:
    story = UserStory(
        id=73230,
        title="Backend API change",
        description="Update endpoint behavior",
        acceptance_criteria=[
            AcceptanceCriteria(order=1, text="API returns 200 on success", id="AC-1"),
            AcceptanceCriteria(order=2, text="API returns 400 on invalid input"),
        ],
        state="Active",
        area_path="Project\\API",
        tags=["api", "backend"],
    )
    assert len(story.acceptance_criteria) == 2
    assert story.acceptance_criteria[0].id == "AC-1"


def test_bug_requires_positive_id() -> None:
    with pytest.raises(ValidationError):
        Bug(id=0, title="Null ref", state="Active")


def test_feature_and_requirement_analysis() -> None:
    feature = FeatureAnalysis(
        feature_type=FeatureType.BACKEND_API,
        risk_level=RiskLevel.HIGH,
        business_rules=["Reject invalid payloads"],
        modules=["OrdersApi"],
        applicable_optional_categories=[TestCategory.API, TestCategory.INTEGRATION],
        excluded_optional_categories=[TestCategory.UI, TestCategory.DATABASE],
        rationale="Backend API only",
    )
    analysis = RequirementAnalysis(
        user_story_id=73230,
        feature_analysis=feature,
        requirement_gaps=[],
        qa_strategy=_strategy(),
        blocked=False,
    )
    assert analysis.modules == ["OrdersApi"]


def test_requirement_analysis_rejects_blocking_gap_without_blocked_flag() -> None:
    feature = FeatureAnalysis(
        feature_type=FeatureType.BACKEND_API,
        risk_level=RiskLevel.HIGH,
        rationale="Backend API only",
    )
    with pytest.raises(ValidationError):
        RequirementAnalysis(
            user_story_id=73230,
            feature_analysis=feature,
            requirement_gaps=[
                RequirementGap(
                    type=RequirementGapType.AMBIGUOUS_AC,
                    severity=GapSeverity.BLOCKING,
                    description="AC unclear",
                    evidence="AC section empty",
                )
            ],
            qa_strategy=_strategy(blocked=False, estimates=CoverageEstimates()),
            blocked=False,
        )


def test_qa_strategy_rejects_overlapping_categories() -> None:
    with pytest.raises(ValidationError):
        _strategy(
            testing_not_required=[
                CategoryExclusion(category=TestCategory.API, reason="overlap")
            ]
        )


def test_coverage_report_final_estimates_match_missing() -> None:
    missing = [
        ScenarioRef(
            key="m1",
            title="Missing negative path",
            source=ScenarioSource.MISSING,
            category=TestCategory.NEGATIVE,
        )
    ]
    report = CoverageReport(
        user_story_id=73230,
        missing_scenarios=missing,
        qa_strategy_final=_strategy(
            estimates=CoverageEstimates(
                estimated_new_test_cases=1,
                estimated_existing_coverage=0,
                estimated_duplicate_scenarios=0,
                preliminary=False,
            )
        ),
        generation_directive=GenerationDirective.GAP_FILL_ONLY,
    )
    assert len(report.missing_scenarios) == 1


def test_duplicate_analysis_from_clusters() -> None:
    canonical = ScenarioRef(
        key="c1", title="Verify Login", source=ScenarioSource.EXISTING
    )
    duplicate = ScenarioRef(
        key="c2",
        title="Verify successful authentication",
        source=ScenarioSource.SIMILAR,
    )
    analysis = DuplicateAnalysis.from_clusters(
        user_story_id=73230,
        clusters=[
            DuplicateCluster(
                canonical=canonical,
                duplicates=[duplicate],
                similarity=0.91,
                basis=DuplicateBasis.INTENT,
            )
        ],
    )
    assert analysis.duplicate_scenario_count == 1


def test_validation_result_success_and_failure() -> None:
    ok = ValidationResult.success()
    assert ok.is_valid is True

    bad = ValidationResult.failure(
        [
            ValidationIssue(
                code="VALIDATION_STEP_MISMATCH",
                message="step_count != expected_result_count",
                field="steps",
            )
        ]
    )
    assert bad.is_valid is False

    with pytest.raises(ValidationError):
        ValidationResult(is_valid=True, errors=[ValidationIssue(code="X", message="y")])
