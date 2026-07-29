"""MCP tool: analyze_requirement."""

from __future__ import annotations

from typing import Any

from qa_intelligence.mcp import responses
from qa_intelligence.mcp.parsers import parse_user_story
from qa_intelligence.mcp.runtime import get_container
from qa_intelligence.prompts.analysis_guidance import analysis_guidance


async def analyze_requirement(
    user_story_id: int | None = None,
    user_story: dict[str, Any] | None = None,
) -> dict[str, object]:
    """Analyze a User Story and produce a QA Strategy plus requirement gaps.

    Provide either ``user_story_id`` or an embedded ``user_story`` payload.
    """
    try:
        container = get_container()
        if user_story is not None:
            story = parse_user_story(user_story)
            analysis = container.requirement_analysis_service.analyze_story(story)
        elif user_story_id is not None:
            analysis = await container.requirement_analysis_service.analyze(
                user_story_id=user_story_id
            )
        else:
            return responses.failure(
                "VALIDATION_ERROR",
                "Provide user_story_id or user_story",
            ).model_dump(mode="json")

        response = responses.success(analysis, warnings=[analysis_guidance()])
        return response.model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        return responses.from_exception(exc, tool_name="analyze_requirement").model_dump(
            mode="json"
        )
