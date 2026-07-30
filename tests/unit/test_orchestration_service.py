"""Unit tests for OrchestrationService end-to-end workflow."""

from __future__ import annotations

import pytest

from qa_intelligence.domain.enums import CreateStatus, GenerationDirective, LinkStatus
from qa_intelligence.domain.models.bug import Bug
from qa_intelligence.domain.models.orchestration import WorkflowStepName, WorkflowStepStatus
from qa_intelligence.domain.models.read_models import TestCaseSummary
from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.domain.models.user_story import AcceptanceCriteria, UserStory
from qa_intelligence.infrastructure.errors import NotFoundError
from qa_intelligence.services.bug_service import BugService
from qa_intelligence.services.coverage_analysis_service import CoverageAnalysisService
from qa_intelligence.services.duplicate_detection_service import DuplicateDetectionService
from qa_intelligence.services.linking_service import LinkingService
from qa_intelligence.services.orchestration_service import OrchestrationService
from qa_intelligence.services.requirement_analysis_service import RequirementAnalysisService
from qa_intelligence.services.story_service import StoryService
from qa_intelligence.services.test_case_generation_service import TestCaseGenerationService
from qa_intelligence.services.test_case_service import TestCaseService
from qa_intelligence.services.test_strategy_service import TestStrategyService


class FakeUserStoryRepository:
    def __init__(self, stories: dict[int, UserStory]) -> None:
        self.stories = stories

    async def get_by_id(self, user_story_id: int) -> UserStory:
        if user_story_id not in self.stories:
            raise NotFoundError(f"User story {user_story_id} not found")
        return self.stories[user_story_id]

    async def get_related_work_items(
        self,
        user_story_id: int,
        link_types: list[str] | None = None,
    ) -> list:
        return []


class FakeTestCaseRepository:
    def __init__(
        self,
        existing: dict[int, list[TestCaseSummary]] | None = None,
    ) -> None:
        self.existing = existing or {}
        self.created: list[TestCase] = []
        self.links: list[tuple[int, int]] = []
        self._next_id = 1000

    async def get_by_id(self, test_case_id: int) -> TestCaseSummary:
        raise NotFoundError(f"Test case {test_case_id} not found")

    async def list_linked_to_story(self, user_story_id: int) -> list[TestCaseSummary]:
        return list(self.existing.get(user_story_id, []))

    async def search(
        self,
        query: str,
        *,
        area_path: str | None = None,
        top: int = 25,
    ) -> list[TestCaseSummary]:
        return []

    async def create(self, draft: TestCase) -> int:
        self._next_id += 1
        self.created.append(draft)
        return self._next_id

    async def link_to_user_story(self, user_story_id: int, test_case_id: int) -> None:
        self.links.append((user_story_id, test_case_id))

    async def add_to_suite(self, suite_id: int, test_case_id: int) -> None:
        return None


class FakeBugRepository:
    def __init__(self, bugs: dict[int, list[Bug]] | None = None) -> None:
        self.bugs = bugs or {}

    async def get_by_id(self, bug_id: int) -> Bug:
        raise NotFoundError(f"Bug {bug_id} not found")

    async def list_related_to_story(self, user_story_id: int) -> list[Bug]:
        return list(self.bugs.get(user_story_id, []))


def _complete_story(story_id: int = 73230) -> UserStory:
    return UserStory(
        id=story_id,
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


def _blocked_story(story_id: int = 99) -> UserStory:
    return UserStory(
        id=story_id,
        title="Something vague",
        description="TBD",
        acceptance_criteria=[],
    )


def _build_orchestration(
    *,
    stories: dict[int, UserStory],
    existing: dict[int, list[TestCaseSummary]] | None = None,
    bugs: dict[int, list[Bug]] | None = None,
) -> tuple[OrchestrationService, FakeTestCaseRepository]:
    story_repo = FakeUserStoryRepository(stories)
    tc_repo = FakeTestCaseRepository(existing)
    bug_repo = FakeBugRepository(bugs)

    orchestration = OrchestrationService(
        story_service=StoryService(story_repo),
        requirement_analysis_service=RequirementAnalysisService(story_repo),
        test_case_service=TestCaseService(tc_repo),
        bug_service=BugService(bug_repo),
        duplicate_detection_service=DuplicateDetectionService(),
        coverage_analysis_service=CoverageAnalysisService(),
        test_strategy_service=TestStrategyService(),
        test_case_generation_service=TestCaseGenerationService(),
        linking_service=LinkingService(tc_repo),
    )
    return orchestration, tc_repo


@pytest.mark.asyncio
async def test_full_workflow_fresh_suite_publishes_and_links() -> None:
    story = _complete_story()
    orch, tc_repo = _build_orchestration(stories={story.id: story})

    summary = await orch.run(story.id, dry_run=False)

    assert summary.ok is True
    assert summary.blocked is False
    assert summary.user_story is not None
    assert summary.requirement_analysis is not None
    assert summary.test_strategy is not None
    assert summary.generation is not None
    assert summary.created_ids
    assert summary.linked_ids == summary.created_ids
    assert len(tc_repo.created) == len(summary.created_ids)
    assert all(r.status == CreateStatus.CREATED for r in summary.create_results)
    assert all(r.status == LinkStatus.LINKED for r in summary.link_results)

    step_names = [s.name for s in summary.steps]
    assert step_names == list(WorkflowStepName)
    assert all(s.status != WorkflowStepStatus.FAILED for s in summary.steps)
    # Code intelligence is skipped when no repository_path is provided.
    code_step = next(s for s in summary.steps if s.name == WorkflowStepName.CODE_INTELLIGENCE)
    assert code_step.status == WorkflowStepStatus.SKIPPED
    assert all(
        s.status != WorkflowStepStatus.SKIPPED
        for s in summary.steps
        if s.name != WorkflowStepName.CODE_INTELLIGENCE
    )


@pytest.mark.asyncio
async def test_dry_run_validates_without_ado_writes() -> None:
    story = _complete_story()
    orch, tc_repo = _build_orchestration(stories={story.id: story})

    summary = await orch.run(story.id, dry_run=True)

    assert summary.ok is True
    assert summary.dry_run is True
    assert summary.validated_test_cases
    assert summary.created_ids == []
    assert tc_repo.created == []
    assert tc_repo.links == []
    publish_step = next(
        s for s in summary.steps if s.name == WorkflowStepName.PUBLISH_TO_AZURE_DEVOPS
    )
    assert "dry_run" in publish_step.message


@pytest.mark.asyncio
async def test_blocked_requirement_stops_before_inventory() -> None:
    story = _blocked_story()
    orch, _ = _build_orchestration(stories={story.id: story})

    summary = await orch.run(story.id)

    assert summary.ok is False
    assert summary.blocked is True
    assert summary.generation_directive == GenerationDirective.BLOCKED
    assert summary.created_ids == []

    statuses = {s.name: s.status for s in summary.steps}
    assert statuses[WorkflowStepName.FETCH_USER_STORY] == WorkflowStepStatus.SUCCEEDED
    assert statuses[WorkflowStepName.ANALYZE_REQUIREMENT] == WorkflowStepStatus.BLOCKED
    assert statuses[WorkflowStepName.GENERATE_TEST_CASES] == WorkflowStepStatus.SKIPPED
    assert statuses[WorkflowStepName.PUBLISH_TO_AZURE_DEVOPS] == WorkflowStepStatus.SKIPPED


@pytest.mark.asyncio
async def test_gap_fill_when_existing_present() -> None:
    story = _complete_story()
    existing = [
        TestCaseSummary(
            id=10,
            title="API returns 200 when payload is valid",
            steps=["Send valid payload"],
            expected_results=["200 OK"],
        ),
        TestCaseSummary(
            id=11,
            title="API returns 400 when required fields are missing",
            steps=["Omit required fields"],
            expected_results=["400 Bad Request"],
        ),
        TestCaseSummary(
            id=12,
            title="Invalid JSON is rejected with a clear error message",
            steps=["Send invalid JSON"],
            expected_results=["Clear error message"],
        ),
    ]
    orch, tc_repo = _build_orchestration(
        stories={story.id: story},
        existing={story.id: existing},
    )

    summary = await orch.run(story.id, dry_run=True)

    assert summary.ok is True
    assert summary.existing_test_cases == existing
    assert summary.generation is not None
    if not summary.generation.generated:
        assert summary.created_ids == []
        assert tc_repo.created == []


@pytest.mark.asyncio
async def test_story_not_found_fails_first_step() -> None:
    orch, _ = _build_orchestration(stories={})

    summary = await orch.run(404)

    assert summary.ok is False
    assert len(summary.steps) == 1
    assert summary.steps[0].name == WorkflowStepName.FETCH_USER_STORY
    assert summary.steps[0].status == WorkflowStepStatus.FAILED


@pytest.mark.asyncio
async def test_publish_disabled_stops_after_validation() -> None:
    story = _complete_story()
    orch, tc_repo = _build_orchestration(stories={story.id: story})

    summary = await orch.run(story.id, publish=False)

    assert summary.ok is True
    assert summary.validated_test_cases
    assert summary.created_ids == []
    assert tc_repo.created == []
    publish_step = next(
        s for s in summary.steps if s.name == WorkflowStepName.PUBLISH_TO_AZURE_DEVOPS
    )
    assert publish_step.status == WorkflowStepStatus.SKIPPED
