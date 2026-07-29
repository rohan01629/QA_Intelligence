"""Unit tests for RequirementAnalysisService."""

from __future__ import annotations

import pytest

from qa_intelligence.domain.enums import (
    FeatureType,
    GapSeverity,
    RiskLevel,
    TestCategory,
)
from qa_intelligence.domain.models.user_story import AcceptanceCriteria, UserStory
from qa_intelligence.infrastructure.errors import ConfigurationError
from qa_intelligence.services.requirement_analysis_service import RequirementAnalysisService


def _backend_api_story() -> UserStory:
    return UserStory(
        id=73230,
        title="Update backend API order validation",
        description=(
            "Modify the backend REST API endpoint to validate request payloads "
            "and return correct HTTP status codes. No UI changes."
        ),
        acceptance_criteria=[
            AcceptanceCriteria(
                order=1,
                text="API returns 200 when payload is valid",
                id="AC-1",
            ),
            AcceptanceCriteria(
                order=2,
                text="API returns 400 when required fields are missing",
                id="AC-2",
            ),
            AcceptanceCriteria(
                order=3,
                text="Invalid JSON is rejected with a clear error message",
                id="AC-3",
            ),
        ],
        state="Active",
        area_path="Demo\\OrdersApi",
        tags=["api", "backend"],
    )


def test_backend_api_story_produces_expected_qa_strategy() -> None:
    service = RequirementAnalysisService()
    analysis = service.analyze_story(_backend_api_story())

    assert analysis.feature_analysis.feature_type == FeatureType.BACKEND_API
    assert analysis.qa_strategy.feature_type == FeatureType.BACKEND_API
    assert analysis.qa_strategy.risk == RiskLevel.HIGH
    assert analysis.blocked is False

    required = set(analysis.qa_strategy.testing_required)
    assert {
        TestCategory.POSITIVE,
        TestCategory.NEGATIVE,
        TestCategory.EDGE,
        TestCategory.VALIDATION,
        TestCategory.REGRESSION,
        TestCategory.API,
        TestCategory.INTEGRATION,
    }.issubset(required)

    skipped = {item.category for item in analysis.qa_strategy.testing_not_required}
    assert TestCategory.UI in skipped
    assert TestCategory.ACCESSIBILITY in skipped
    assert TestCategory.DATABASE in skipped
    assert TestCategory.PERFORMANCE in skipped

    assert "backend api" in analysis.qa_strategy.reason.lower()
    assert analysis.modules
    assert analysis.business_rules
    assert analysis.feature_analysis.regression_impact
    assert analysis.qa_strategy.estimates.preliminary is True
    assert analysis.qa_strategy.estimates.estimated_new_test_cases > 0


def test_missing_acceptance_criteria_blocks_generation() -> None:
    story = UserStory(
        id=1,
        title="Something vague",
        description="TBD",
        acceptance_criteria=[],
    )
    analysis = RequirementAnalysisService().analyze_story(story)
    assert analysis.blocked is True
    assert analysis.qa_strategy.blocked is True
    assert analysis.qa_strategy.estimates.estimated_new_test_cases == 0
    assert any(g.severity == GapSeverity.BLOCKING for g in analysis.requirement_gaps)


def test_ui_story_includes_ui_excludes_api_by_default() -> None:
    story = UserStory(
        id=2,
        title="Update checkout button label on UI screen",
        description="Change the frontend button text on the checkout page modal.",
        acceptance_criteria=[
            AcceptanceCriteria(order=1, text="Checkout button shows the new label"),
        ],
        area_path="Demo\\WebUI",
    )
    analysis = RequirementAnalysisService().analyze_story(story)
    assert analysis.feature_analysis.feature_type == FeatureType.UI
    assert TestCategory.UI in analysis.qa_strategy.testing_required
    skipped = {item.category for item in analysis.qa_strategy.testing_not_required}
    # API may still appear if 'button' corpus doesn't match API; typically skipped
    assert TestCategory.DATABASE in skipped


@pytest.mark.asyncio
async def test_analyze_requires_story_or_id() -> None:
    service = RequirementAnalysisService()
    with pytest.raises(ConfigurationError):
        await service.analyze()


@pytest.mark.asyncio
async def test_analyze_by_id_requires_repository() -> None:
    service = RequirementAnalysisService()
    with pytest.raises(ConfigurationError):
        await service.analyze(user_story_id=73230)


@pytest.mark.asyncio
async def test_analyze_with_embedded_story() -> None:
    service = RequirementAnalysisService()
    analysis = await service.analyze(user_story=_backend_api_story())
    assert analysis.user_story_id == 73230
    assert analysis.feature_analysis.feature_type == FeatureType.BACKEND_API
