"""MCP tool: get_related_bugs."""

from __future__ import annotations

from qa_intelligence.mcp import responses
from qa_intelligence.mcp.runtime import get_container


async def get_related_bugs(user_story_id: int) -> dict[str, object]:
    """Fetch bugs related to a User Story for regression coverage signals."""
    try:
        container = get_container()
        bugs = await container.bug_service.list_related(user_story_id)
        return responses.success(bugs).model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        return responses.from_exception(exc, tool_name="get_related_bugs").model_dump(mode="json")
