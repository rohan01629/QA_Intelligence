"""Unit tests for TestCaseGenerationService."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from qa_intelligence.domain.enums import (
    FeatureType,
    GenerationDirective,
    RiskLevel,
    ScenarioSource,
    TestCategory,
)
from qa_intelligence.domain.models.coverage import ScenarioRef
from qa_intelligence.domain.models.generation import GenerationMode
from qa_intelligence.domain.models.qa_strategy import CoverageEstimates, QAStrategy
from qa_intelligence.domain.models.read_models import TestCaseSummary
from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.domain.models.test_strategy import (
    CategoryDecision,
    RiskBasedTestingStrategy,
    TestStrategy,
)
from qa_intelligence.domain.models.user_story import AcceptanceCriteria, UserStory
from qa_intelligence.domain.validation.test_case_validator import validate_test_case_payload
from qa_intelligence.services.test_case_generation_service import TestCaseGenerationService


def _strategy(
    *,
    directive: GenerationDirective = GenerationDirective.FRESH_SUITE,
    estimated_new: int = 6,
    blocked: bool = False,
) -> TestStrategy:
    categories = [
        TestCategory.POSITIVE,
        TestCategory.NEGATIVE,
        TestCategory.EDGE,
        TestCategory.VALIDATION,
        TestCategory.REGRESSION,
        TestCategory.API,
    ]
    qa = QAStrategy(
        feature_type=FeatureType.BACKEND_API,
        risk=RiskLevel.HIGH,
        testing_required=categories,
        testing_not_required=[],
        reason="Backend API strategy",
        estimates=CoverageEstimates(
            estimated_new_test_cases=0 if blocked else estimated_new,
            preliminary=False,
        ),
        blocked=blocked,
    )
    return TestStrategy(
        user_story_id=1,
        feature_type=FeatureType.BACKEND_API,
        risk_level=RiskLevel.HIGH,
        applicable_categories=[
            CategoryDecision(category=c, applicable=True, reason=f"{c.value} required")
            for c in categories
        ],
        skipped_categories=[],
        estimated_new_test_cases=0 if blocked else estimated_new,
        estimated_existing_coverage=0,
        estimated_duplicate_scenarios=0,
        risk_based_strategy=RiskBasedTestingStrategy(
            risk_level=RiskLevel.HIGH,
            depth_guidance="High risk depth",
            regression_emphasis="Protect API regressions",
            priority_order=categories,
            recommended_cases_per_uncovered_scenario=1.3,
        ),
        narrative_summary="Backend API high-risk strategy",
        blocked=blocked,
        generation_directive=GenerationDirective.BLOCKED if blocked else directive,
        estimates=qa.estimates,
        qa_strategy=qa,
    )


def _story() -> UserStory:
    return UserStory(
        id=1,
        title="Order API validation",
        acceptance_criteria=[
            AcceptanceCriteria(order=1, text="API returns 200 for valid payload", id="AC-1"),
            AcceptanceCriteria(order=2, text="API returns 400 for missing fields", id="AC-2"),
        ],
    )


def test_fresh_suite_when_no_existing_tests() -> None:
    service = TestCaseGenerationService()
    result = service.generate(
        _strategy(directive=GenerationDirective.FRESH_SUITE, estimated_new=4),
        _story(),
        existing_test_cases=[],
    )
    assert result.mode == GenerationMode.FRESH_SUITE
    assert result.blocked is False
    assert len(result.generated) == 4
    for case in result.generated:
        assert case.step_count == case.expected_result_count
        assert case.title
        assert case.steps
        assert case.expected_results
        # Only three fields in serialized contract
        assert set(case.model_dump().keys()) == {"title", "steps", "expected_results"}


def test_gap_fill_only_missing_scenarios_when_existing_exist() -> None:
    service = TestCaseGenerationService()
    existing = [
        TestCaseSummary(
            id=10,
            title="API returns 200 for valid payload",
            steps=["Send valid"],
            expected_results=["200 OK"],
        )
    ]
    uncovered = [
        ScenarioRef(
            key="AC-2",
            title="API returns 400 for missing fields",
            source=ScenarioSource.MISSING,
        )
    ]
    result = service.generate(
        _strategy(directive=GenerationDirective.GAP_FILL_ONLY, estimated_new=3),
        _story(),
        existing_test_cases=existing,
        uncovered_scenarios=uncovered,
    )
    assert result.mode == GenerationMode.GAP_FILL_ONLY
    assert result.generated
    assert all("400" in r.source_scenario_key or r.source_scenario_key == "AC-2" for r in result.records if not r.rejected)
    assert all(c.step_count == c.expected_result_count for c in result.generated)


def test_gap_fill_without_uncovered_generates_nothing() -> None:
    result = TestCaseGenerationService().generate(
        _strategy(directive=GenerationDirective.GAP_FILL_ONLY, estimated_new=5),
        _story(),
        existing_test_cases=[
            TestCaseSummary(id=1, title="Existing", steps=["a"], expected_results=["b"])
        ],
        uncovered_scenarios=[],
    )
    assert result.mode == GenerationMode.GAP_FILL_ONLY
    assert result.generated == []


def test_blocked_strategy_generates_nothing() -> None:
    result = TestCaseGenerationService().generate(
        _strategy(blocked=True),
        _story(),
        existing_test_cases=[],
    )
    assert result.mode == GenerationMode.BLOCKED
    assert result.generated == []


def test_validator_rejects_step_mismatch() -> None:
    case, validation = validate_test_case_payload(
        {
            "title": "Bad case",
            "steps": ["one", "two"],
            "expected_results": ["only one"],
        }
    )
    assert case is None
    assert validation.is_valid is False
    assert any(e.code == "VALIDATION_STEP_MISMATCH" for e in validation.errors)


def test_test_case_model_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        TestCase.model_validate(
            {
                "title": "x",
                "steps": ["a"],
                "expected_results": ["b"],
                "priority": "high",
            }
        )
