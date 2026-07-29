"""MCP tool: get_existing_test_cases."""

from __future__ import annotations

from qa_intelligence.mcp import responses
from qa_intelligence.mcp.runtime import get_container


async def get_existing_test_cases(user_story_id: int) -> dict[str, object]:
    """List test cases already linked to a User Story in Azure DevOps."""
    try:
        container = get_container()
        cases = await container.test_case_service.list_existing(user_story_id)
        return responses.success(cases).model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        return responses.from_exception(exc, tool_name="get_existing_test_cases").model_dump(
            mode="json"
        )
