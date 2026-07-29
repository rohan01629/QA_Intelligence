"""MCP tool: get_user_story."""

from __future__ import annotations

from qa_intelligence.mcp import responses
from qa_intelligence.mcp.runtime import get_container


async def get_user_story(work_item_id: int) -> dict[str, object]:
    """Fetch a User Story from Azure DevOps by work item ID.

    Returns title, description, acceptance criteria, state, area path,
    iteration path, and tags.
    """
    try:
        container = get_container()
        story = await container.story_service.get_user_story(work_item_id)
        return responses.success(story).model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        return responses.from_exception(exc, tool_name="get_user_story").model_dump(mode="json")
