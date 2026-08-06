"""Unit tests for product rules enforcement."""

from __future__ import annotations

from qa_intelligence.domain.enums import (
    FeatureType,
    GenerationDirective,
    RiskLevel,
    TestCategory,
)
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
from qa_intelligence.domain.policies.product_rules import (
    CORE_CATEGORIES_ORDERED,
    PRODUCT_RULES,
    TEST_CASE_ALLOWED_FIELDS,
)
from qa_intelligence.domain.validation.duplicate_guard import (
    find_intra_batch_duplicates,
    is_duplicate_of_existing,
)
from qa_intelligence.domain.validation.test_case_validator import validate_test_case_payload
from qa_intelligence.services.test_case_generation_service import TestCaseGenerationService
from qa_intelligence.services.test_case_service import TestCaseService


def test_product_rules_catalog_has_thirteen_rules() -> None:
    assert len(PRODUCT_RULES) == 13
    assert CORE_CATEGORIES_ORDERED == (
        TestCategory.POSITIVE,
        TestCategory.NEGATIVE,
        TestCategory.EDGE,
        TestCategory.VALIDATION,
        TestCategory.REGRESSION,
    )
    assert TEST_CASE_ALLOWED_FIELDS == {
        "title",
        "steps",
        "expected_results",
        "is_regression",
        "is_sanity",
    }


def _strategy(*, estimated_new: int = 4) -> TestStrategy:
    categories = list(CORE_CATEGORIES_ORDERED) + [TestCategory.API]
    qa = QAStrategy(
        feature_type=FeatureType.BACKEND_API,
        risk=RiskLevel.HIGH,
        testing_required=categories,
        testing_not_required=[],
        reason="Backend API strategy",
        estimates=CoverageEstimates(estimated_new_test_cases=estimated_new, preliminary=False),
    )
    return TestStrategy(
        user_story_id=1,
        feature_type=FeatureType.BACKEND_API,
        risk_level=RiskLevel.HIGH,
        applicable_categories=[
            CategoryDecision(category=c, applicable=True, reason=f"{c.value} required")
            for c in categories
        ],
        skipped_categories=[
            CategoryDecision(
                category=TestCategory.UI,
                applicable=False,
                reason="No UI signals",
            )
        ],
        estimated_new_test_cases=estimated_new,
        risk_based_strategy=RiskBasedTestingStrategy(
            risk_level=RiskLevel.HIGH,
            depth_guidance="High risk depth",
            regression_emphasis="Protect API regressions",
            priority_order=categories,
        ),
        narrative_summary="Backend API high-risk strategy",
        generation_directive=GenerationDirective.FRESH_SUITE,
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


def test_rule_2_fresh_suite_when_no_existing() -> None:
    result = TestCaseGenerationService().generate(
        _strategy(),
        _story(),
        existing_test_cases=[],
    )
    assert result.mode == GenerationMode.FRESH_SUITE
    assert result.generated
    for case in result.generated:
        assert set(case.model_dump().keys()) == TEST_CASE_ALLOWED_FIELDS
        assert case.step_count == case.expected_result_count


def test_rule_3_existing_forces_gap_fill_even_if_directive_fresh() -> None:
    existing = [
        TestCaseSummary(
            id=10,
            title="API returns 200 for valid payload",
            steps=["Send valid"],
            expected_results=["200 OK"],
        )
    ]
    result = TestCaseGenerationService().generate(
        _strategy(estimated_new=3),
        _story(),
        existing_test_cases=existing,
        uncovered_scenarios=[],
    )
    assert result.mode == GenerationMode.GAP_FILL_ONLY
    assert result.generated == []


def test_rule_1_rejects_duplicate_against_existing() -> None:
    existing = [
        TestCaseSummary(
            id=10,
            title="Verify API returns 200 for valid payload - Positive",
            steps=["a", "b", "c"],
            expected_results=["1", "2", "3"],
        )
    ]
    # Force a small budget and uncovered scenario that templates will name similarly.
    from qa_intelligence.domain.models.coverage import ScenarioRef
    from qa_intelligence.domain.enums import ScenarioSource

    result = TestCaseGenerationService().generate(
        _strategy(estimated_new=2),
        _story(),
        existing_test_cases=existing,
        uncovered_scenarios=[
            ScenarioRef(
                key="AC-1",
                title="API returns 200 for valid payload",
                source=ScenarioSource.MISSING,
            )
        ],
    )
    # Positive template title matches existing → rejected as duplicate; others may pass.
    assert any(
        r.rejected and r.validation.errors and r.validation.errors[0].code == "DUPLICATE_TEST_CASE"
        for r in result.records
    )


def test_rules_7_8_9_reject_step_mismatch_and_extra_fields() -> None:
    case, validation = validate_test_case_payload(
        {"title": "x", "steps": ["a", "b"], "expected_results": ["only one"]}
    )
    assert case is None
    assert validation.is_valid is False

    case2, validation2 = validate_test_case_payload(
        {
            "title": "x",
            "steps": ["a"],
            "expected_results": ["b"],
            "priority": "high",
        }
    )
    assert case2 is None
    assert any(e.code == "VALIDATION_EXTRA_FIELDS" for e in validation2.errors)


def test_rule_1_create_rejects_intra_batch_duplicates() -> None:
    class _Repo:
        async def list_linked_to_story(self, user_story_id: int):
            return []

        async def create(self, draft: TestCase) -> int:
            return 1

        async def get_by_id(self, test_case_id: int):
            raise NotImplementedError

        async def search(self, query: str, *, area_path=None, top=25):
            return []

        async def link_to_user_story(self, user_story_id: int, test_case_id: int) -> None:
            return None

        async def add_to_suite(self, suite_id: int, test_case_id: int) -> None:
            return None

    draft = {
        "title": "Same case",
        "steps": ["Do thing"],
        "expected_results": ["Thing done"],
    }
    service = TestCaseService(_Repo())  # type: ignore[arg-type]
    validated, results = service.validate_many([draft, draft], reject_duplicates=True)
    assert len(validated) == 1
    assert results[0].status.value == "validated_only"
    assert results[1].status.value == "rejected"
    assert "Duplicate" in results[1].validation_errors[0]


def test_duplicate_guard_exact_title() -> None:
    draft = TestCase(title="Login works", steps=["Open"], expected_results=["Shown"])
    existing = [
        TestCaseSummary(id=1, title="Login works", steps=["x"], expected_results=["y"])
    ]
    is_dup, score, matched = is_duplicate_of_existing(draft, existing)
    assert is_dup is True
    assert score == 1.0
    assert matched is not None


def test_intra_batch_duplicate_map() -> None:
    a = TestCase(title="A", steps=["1"], expected_results=["1"])
    b = TestCase(title="A", steps=["1"], expected_results=["1"])
    mapping = find_intra_batch_duplicates([a, b])
    assert mapping == {1: 0}
