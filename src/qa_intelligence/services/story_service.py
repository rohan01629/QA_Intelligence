"""StoryService — fetch and normalize user stories."""

from __future__ import annotations

import structlog

from qa_intelligence.domain.models.user_story import UserStory
from qa_intelligence.repositories.protocols import UserStoryRepository

logger = structlog.get_logger(__name__)


class StoryService:
    """Load user stories via the UserStoryRepository port."""

    def __init__(self, user_story_repository: UserStoryRepository) -> None:
        self._user_story_repository = user_story_repository

    async def get_user_story(self, user_story_id: int) -> UserStory:
        story = await self._user_story_repository.get_by_id(user_story_id)
        logger.info("story.fetched", user_story_id=story.id, ac_count=len(story.acceptance_criteria))
        return story
