"""Azure DevOps User Story repository — data access only."""

from __future__ import annotations

import structlog

from qa_intelligence.domain.models.read_models import RelatedWorkItemRef
from qa_intelligence.domain.models.user_story import UserStory
from qa_intelligence.infrastructure.ado.client import AzureDevOpsClient
from qa_intelligence.infrastructure.ado.mappers import map_related_refs, map_user_story

logger = structlog.get_logger(__name__)


class AdoUserStoryRepository:
    """UserStoryRepository adapter backed by Azure DevOps WIT APIs."""

    def __init__(self, client: AzureDevOpsClient) -> None:
        self._client = client

    async def get_by_id(self, user_story_id: int) -> UserStory:
        payload = await self._client.get_work_item(user_story_id)
        story = map_user_story(payload, self._client.settings)
        logger.info("ado.user_story_fetched", user_story_id=story.id)
        return story

    async def get_related_work_items(
        self,
        user_story_id: int,
        link_types: list[str] | None = None,
    ) -> list[RelatedWorkItemRef]:
        payload = await self._client.get_work_item(user_story_id, expand="relations")
        refs = map_related_refs(payload)
        if link_types is not None:
            allowed = set(link_types)
            refs = [ref for ref in refs if ref.link_type in allowed]
        logger.info(
            "ado.user_story_relations_fetched",
            user_story_id=user_story_id,
            count=len(refs),
        )
        return refs
