"""MCP tool: search_similar_test_cases."""

from __future__ import annotations

from qa_intelligence.mcp import responses
from qa_intelligence.mcp.runtime import get_container


async def search_similar_test_cases(
    query: str,
    area_path: str | None = None,
    top: int = 25,
) -> dict[str, object]:
    """Search the Azure DevOps project for similar test cases by title text."""
    try:
        container = get_container()
        results = await container.test_case_repository.search(
            query,
            area_path=area_path,
            top=top,
        )
        payload = [
            {
                **case.model_dump(mode="json"),
                "similarity_score": None,
                "match_signals": ["title_contains"],
            }
            for case in results
        ]
        return responses.success(payload).model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        return responses.from_exception(exc, tool_name="search_similar_test_cases").model_dump(
            mode="json"
        )
