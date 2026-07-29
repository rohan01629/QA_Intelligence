"""MCP tool: create_test_cases."""

from __future__ import annotations

from typing import Any

from qa_intelligence.mcp import responses
from qa_intelligence.mcp.parsers import parse_test_cases
from qa_intelligence.mcp.runtime import get_container
from qa_intelligence.prompts.analysis_guidance import generation_guidance


async def create_test_cases(
    test_cases: list[Any],
    dry_run: bool = False,
    reject_duplicates: bool = True,
    override_requirement_block: bool = False,
    requirement_blocked: bool = False,
    user_story_id: int | None = None,
) -> dict[str, object]:
    """Validate and create Test Cases in Azure DevOps.

    Each test case must contain ONLY title, steps, and expected_results,
    with step_count == expected_result_count.
    """
    try:
        container = get_container()
        drafts = parse_test_cases(test_cases)
        existing = None
        if user_story_id is not None and reject_duplicates:
            existing = await container.test_case_service.list_existing(user_story_id)

        results = await container.test_case_service.create_many(
            drafts,
            dry_run=dry_run,
            requirement_blocked=requirement_blocked,
            override_requirement_block=override_requirement_block,
            reject_duplicates=reject_duplicates,
            existing_test_cases=existing,
        )
        return responses.success(
            results,
            warnings=[generation_guidance()],
        ).model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        return responses.from_exception(exc, tool_name="create_test_cases").model_dump(mode="json")
