"""MCP tool: analyze_codebase."""

from __future__ import annotations

from typing import Any

from qa_intelligence.mcp import responses
from qa_intelligence.mcp.parsers import parse_bugs, parse_user_story
from qa_intelligence.mcp.runtime import get_container
from qa_intelligence.prompts.analysis_guidance import product_rules_guidance


async def analyze_codebase(
    repository_path: str,
    user_story_id: int | None = None,
    user_story: dict[str, Any] | None = None,
    related_bugs: list[dict[str, Any]] | None = None,
    max_files: int | None = None,
) -> dict[str, object]:
    """Analyze a local repository for implementation impact of a User Story.

    Returns an Implementation Summary (affected files, APIs, business rules,
    regression areas). Does not create test cases.
    """
    try:
        container = get_container()
        if user_story is not None:
            story = parse_user_story(user_story)
        elif user_story_id is not None:
            story = await container.story_service.get_user_story(user_story_id)
        else:
            return responses.failure(
                "VALIDATION_ERROR",
                "Provide user_story_id or user_story",
            ).model_dump(mode="json")

        bugs = parse_bugs(related_bugs) if related_bugs is not None else None
        if related_bugs is None and user_story_id is not None:
            bugs = await container.bug_service.list_related(user_story_id)

        summary = container.code_intelligence_service.analyze(
            story,
            repository_path,
            related_bugs=bugs,
            max_files=max_files,
        )
        return responses.success(
            summary,
            warnings=[product_rules_guidance()],
        ).model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        return responses.from_exception(exc, tool_name="analyze_codebase").model_dump(mode="json")
