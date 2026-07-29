"""Repository protocol (port) definitions — Azure DevOps data access only."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from qa_intelligence.domain.models.bug import Bug
from qa_intelligence.domain.models.read_models import RelatedWorkItemRef, TestCaseSummary
from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.domain.models.user_story import UserStory


@runtime_checkable
class UserStoryRepository(Protocol):
    """Fetch user stories and their work-item relations from Azure DevOps."""

    async def get_by_id(self, user_story_id: int) -> UserStory: ...

    async def get_related_work_items(
        self,
        user_story_id: int,
        link_types: list[str] | None = None,
    ) -> list[RelatedWorkItemRef]: ...


@runtime_checkable
class TestCaseRepository(Protocol):
    """Fetch, search, create, and link test cases in Azure DevOps."""

    async def get_by_id(self, test_case_id: int) -> TestCaseSummary: ...

    async def list_linked_to_story(self, user_story_id: int) -> list[TestCaseSummary]: ...

    async def search(
        self,
        query: str,
        *,
        area_path: str | None = None,
        top: int = 25,
    ) -> list[TestCaseSummary]: ...

    async def create(self, draft: TestCase) -> int: ...

    async def link_to_user_story(
        self,
        user_story_id: int,
        test_case_id: int,
    ) -> None: ...

    async def add_to_suite(self, suite_id: int, test_case_id: int) -> None: ...


@runtime_checkable
class BugRepository(Protocol):
    """Fetch bugs and story-related bugs from Azure DevOps."""

    async def get_by_id(self, bug_id: int) -> Bug: ...

    async def list_related_to_story(self, user_story_id: int) -> list[Bug]: ...
