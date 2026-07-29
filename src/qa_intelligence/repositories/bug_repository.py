"""Azure DevOps Bug repository — data access only."""

from __future__ import annotations

import structlog

from qa_intelligence.domain.models.bug import Bug
from qa_intelligence.infrastructure.ado.client import AzureDevOpsClient
from qa_intelligence.infrastructure.ado.mappers import extract_related_ids, map_bug

logger = structlog.get_logger(__name__)


def _escape_wiql(value: str) -> str:
    return value.replace("'", "''")


class AdoBugRepository:
    """BugRepository adapter backed by Azure DevOps WIT APIs."""

    def __init__(self, client: AzureDevOpsClient) -> None:
        self._client = client

    async def get_by_id(self, bug_id: int) -> Bug:
        payload = await self._client.get_work_item(bug_id)
        bug = map_bug(payload)
        logger.info("ado.bug_fetched", bug_id=bug.id)
        return bug

    async def list_related_to_story(self, user_story_id: int) -> list[Bug]:
        """Return bugs linked to the story, plus open bugs under the same area path.

        This is ADO query/filter data access only — no ranking or QA analysis.
        """
        story = await self._client.get_work_item(user_story_id, expand="relations")
        related_ids = [item_id for item_id, _link in extract_related_ids(story)]
        fields = story.get("fields") or {}
        area_path = str(fields.get("System.AreaPath") or "")
        bug_type = self._client.settings.ado_bug_type
        bugs_by_id: dict[int, Bug] = {}

        if related_ids:
            payloads = await self._client.get_work_items_batch(related_ids)
            for payload in payloads:
                payload_fields = payload.get("fields") or {}
                if payload_fields.get("System.WorkItemType") != bug_type:
                    continue
                bug = map_bug(payload)
                bugs_by_id[bug.id] = bug

        if area_path:
            wiql = (
                "SELECT [System.Id] FROM WorkItems WHERE "
                f"[System.WorkItemType] = '{_escape_wiql(bug_type)}' "
                f"AND [System.AreaPath] UNDER '{_escape_wiql(area_path)}' "
                "AND [System.State] <> 'Closed' "
                "ORDER BY [System.ChangedDate] DESC"
            )
            fallback_ids = (await self._client.query_wiql(wiql))[:25]
            missing = [i for i in fallback_ids if i not in bugs_by_id]
            if missing:
                payloads = await self._client.get_work_items_batch(missing)
                for payload in payloads:
                    bug = map_bug(payload)
                    bugs_by_id[bug.id] = bug

        bugs = list(bugs_by_id.values())
        logger.info(
            "ado.bugs_related_to_story",
            user_story_id=user_story_id,
            count=len(bugs),
        )
        return bugs
