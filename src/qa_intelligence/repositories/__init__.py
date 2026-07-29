"""Repository adapters and ports (Azure DevOps data access only)."""

from __future__ import annotations

from qa_intelligence.repositories.bug_repository import AdoBugRepository
from qa_intelligence.repositories.protocols import (
    BugRepository,
    TestCaseRepository,
    UserStoryRepository,
)
from qa_intelligence.repositories.test_case_repository import AdoTestCaseRepository
from qa_intelligence.repositories.user_story_repository import AdoUserStoryRepository

__all__ = [
    "AdoBugRepository",
    "AdoTestCaseRepository",
    "AdoUserStoryRepository",
    "BugRepository",
    "TestCaseRepository",
    "UserStoryRepository",
]
