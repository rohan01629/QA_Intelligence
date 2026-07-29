"""Unit tests for CoverageAnalysisService."""

from __future__ import annotations

from qa_intelligence.domain.enums import ScenarioSource
from qa_intelligence.domain.models.bug import Bug
from qa_intelligence.domain.models.coverage_matrix import CoverageStatus
from qa_intelligence.domain.models.read_models import TestCaseSummary
from qa_intelligence.domain.models.user_story import AcceptanceCriteria, UserStory
from qa_intelligence.services.coverage_analysis_service import CoverageAnalysisService


def _story() -> UserStory:
    return UserStory(
        id=100,
        title="Order API validation",
        acceptance_criteria=[
            AcceptanceCriteria(
                order=1,
                text="API returns 200 for valid payload",
                id="AC-1",
            ),
            AcceptanceCriteria(
                order=2,
                text="API returns 400 for missing fields",
                id="AC-2",
            ),
            AcceptanceCriteria(
                order=3,
                text="Unauthorized caller receives 401",
                id="AC-3",
            ),
        ],
    )


def test_maps_ac_tests_and_bugs() -> None:
    service = CoverageAnalysisService()
    tests = [
        TestCaseSummary(
            id=1,
            title="API returns 200 for valid payload",
            steps=["Send valid payload"],
            expected_results=["API returns 200 for valid payload"],
        )
    ]
    bugs = [
        Bug(
            id=9,
            title="Unauthorized caller receives 401",
            state="Active",
            repro_steps="Call API without token",
        )
    ]
    result = service.analyze(_story(), tests, bugs)

    assert len(result.acceptance_criteria) == 3
    assert len(result.test_cases) == 1
    assert len(result.bugs) == 1
    assert len(result.matrix) == 3


def test_coverage_matrix_and_uncovered_only() -> None:
    service = CoverageAnalysisService()
    tests = [
        TestCaseSummary(
            id=1,
            title="API returns 200 for valid payload",
            steps=["Send valid payload"],
            expected_results=["API returns 200 for valid payload"],
        )
    ]
    bugs = [
        Bug(
            id=9,
            title="Unauthorized caller receives 401",
            state="Active",
            repro_steps="Call API without token",
        )
    ]
    result = service.analyze(_story(), tests, bugs)

    statuses = {row.ac_id: row.status for row in result.matrix}
    assert statuses["AC-1"] == CoverageStatus.COVERED_BY_TEST
    assert statuses["AC-3"] == CoverageStatus.COVERED_BY_BUG
    assert statuses["AC-2"] in {
        CoverageStatus.UNCOVERED,
        CoverageStatus.PARTIAL,
    }

    uncovered_keys = {s.key for s in result.uncovered_scenarios}
    assert "AC-2" in uncovered_keys
    assert "AC-1" not in uncovered_keys
    assert "AC-3" not in uncovered_keys
    assert all(s.source == ScenarioSource.MISSING for s in result.uncovered_scenarios)


def test_uncovered_scenarios_convenience_api() -> None:
    service = CoverageAnalysisService()
    uncovered = service.uncovered_scenarios(_story(), existing_test_cases=[], related_bugs=[])
    assert len(uncovered) == 3
    assert {s.key for s in uncovered} == {"AC-1", "AC-2", "AC-3"}


def test_empty_ac_returns_story_intent_uncovered() -> None:
    story = UserStory(id=2, title="Vague story", acceptance_criteria=[])
    result = CoverageAnalysisService().analyze(story, [], [])
    assert len(result.matrix) == 1
    assert result.matrix[0].status == CoverageStatus.UNCOVERED
    assert len(result.uncovered_scenarios) == 1
