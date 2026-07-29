"""BugService — related bugs for regression coverage signals."""

from __future__ import annotations

import structlog

from qa_intelligence.domain.models.bug import Bug
from qa_intelligence.repositories.protocols import BugRepository

logger = structlog.get_logger(__name__)


class BugService:
    """Load bugs related to a user story."""

    def __init__(self, bug_repository: BugRepository) -> None:
        self._bug_repository = bug_repository

    async def list_related(self, user_story_id: int) -> list[Bug]:
        bugs = await self._bug_repository.list_related_to_story(user_story_id)
        logger.info("bugs.related_fetched", user_story_id=user_story_id, count=len(bugs))
        return bugs
