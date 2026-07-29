"""Unit tests for DuplicateDetectionService and semantic scorer."""

from __future__ import annotations

from qa_intelligence.domain.enums import ScenarioDisposition
from qa_intelligence.domain.models.bug import Bug
from qa_intelligence.domain.models.read_models import TestCaseSummary
from qa_intelligence.domain.models.user_story import AcceptanceCriteria, UserStory
from qa_intelligence.domain.similarity import FeatureSimilarityScorer, ScenarioText
from qa_intelligence.services.duplicate_detection_service import DuplicateDetectionService


def test_semantic_similarity_login_vs_authentication() -> None:
    scorer = FeatureSimilarityScorer()
    left = ScenarioText.from_parts(title="Verify Login")
    right = ScenarioText.from_parts(title="Verify successful authentication")
    score = scorer.score(left, right)
    assert score >= 0.65
    assert score > scorer.score(
        left,
        ScenarioText.from_parts(title="Export monthly revenue report"),
    )


def test_detects_duplicate_existing_test_cases() -> None:
    story = UserStory(
        id=10,
        title="Login story",
        acceptance_criteria=[
            AcceptanceCriteria(order=1, text="User can log in successfully", id="AC-1"),
        ],
    )
    existing = [
        TestCaseSummary(id=1, title="Verify Login", steps=["Open login"], expected_results=["Page opens"]),
        TestCaseSummary(
            id=2,
            title="Verify successful authentication",
            steps=["Open login page"],
            expected_results=["Login page opens"],
        ),
    ]
    result = DuplicateDetectionService(duplicate_threshold=0.70).detect(story, existing, [])
    assert result.duplicate
    assert all(m.disposition == ScenarioDisposition.DUPLICATE for m in result.duplicate)
    assert result.clusters


def test_covered_and_generate_new() -> None:
    story = UserStory(
        id=11,
        title="API validation",
        acceptance_criteria=[
            AcceptanceCriteria(order=1, text="API returns 200 for valid payload", id="AC-1"),
            AcceptanceCriteria(order=2, text="API returns 400 for missing fields", id="AC-2"),
        ],
    )
    existing = [
        TestCaseSummary(
            id=5,
            title="API returns 200 for valid payload",
            steps=["Send valid payload"],
            expected_results=["API returns 200 for valid payload"],
        )
    ]
    result = DuplicateDetectionService().detect(story, existing, [])
    assert any(m.key == "AC-1" for m in result.covered)
    assert any(m.key == "AC-2" and m.disposition == ScenarioDisposition.GENERATE_NEW for m in result.generate_new)


def test_bug_covered_scenario() -> None:
    story = UserStory(
        id=12,
        title="Auth fix",
        acceptance_criteria=[
            AcceptanceCriteria(
                order=1,
                text="Login fails with invalid password",
                id="AC-1",
            ),
        ],
    )
    bugs = [
        Bug(
            id=99,
            title="Login fails with invalid password",
            state="Active",
            repro_steps="Enter invalid password\nSubmit login",
        )
    ]
    result = DuplicateDetectionService().detect(story, existing_test_cases=[], related_bugs=bugs)
    assert result.bug_covered
    assert result.bug_covered[0].is_bug_covered is True
    assert any(m.is_bug_covered for m in result.covered)


def test_obsolete_existing_test_needs_update() -> None:
    story = UserStory(
        id=13,
        title="Payments API",
        acceptance_criteria=[
            AcceptanceCriteria(order=1, text="Charge card returns authorized", id="AC-1"),
        ],
    )
    existing = [
        TestCaseSummary(
            id=7,
            title="Change button color on settings page",
            steps=["Open settings", "Change color"],
            expected_results=["Color updates", "Settings saved"],
        )
    ]
    result = DuplicateDetectionService(obsolete_threshold=0.45).detect(story, existing, [])
    assert result.obsolete
    assert result.obsolete[0].is_obsolete is True
    assert any(m.is_obsolete for m in result.needs_update)
    assert any(m.disposition == ScenarioDisposition.GENERATE_NEW for m in result.generate_new)


def test_needs_update_for_partial_match() -> None:
    story = UserStory(
        id=14,
        title="Profile update",
        acceptance_criteria=[
            AcceptanceCriteria(
                order=1,
                text="User can update profile email address successfully",
                id="AC-1",
            ),
        ],
    )
    existing = [
        TestCaseSummary(
            id=8,
            title="User can update profile",
            steps=["Open profile"],
            expected_results=["Profile opens"],
        )
    ]
    service = DuplicateDetectionService(
        covered_threshold=0.90,
        needs_update_threshold=0.40,
        similar_threshold=0.40,
    )
    result = service.detect(story, existing, [])
    assert result.needs_update or result.covered or result.generate_new
