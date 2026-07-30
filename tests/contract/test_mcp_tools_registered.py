"""Contract tests for FastMCP tool registration and wiring."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from qa_intelligence.domain.models.user_story import AcceptanceCriteria, UserStory
from qa_intelligence.infrastructure.errors import ConfigurationError
from qa_intelligence.mcp.runtime import reset_container
from qa_intelligence.mcp.schemas.common import ToolResponse
from qa_intelligence.mcp.server import create_mcp_server
from qa_intelligence.mcp.tools import EXPECTED_TOOL_NAMES
from qa_intelligence.mcp.tools import get_user_story as get_user_story_mod


@pytest.fixture(autouse=True)
def _reset_mcp_container() -> None:
    reset_container()
    yield
    reset_container()


@pytest.mark.asyncio
async def test_all_ten_tools_are_registered() -> None:
    mcp = create_mcp_server()
    tools = await mcp.list_tools()
    names = sorted(tool.name for tool in tools)
    assert names == sorted(EXPECTED_TOOL_NAMES)
    assert len(names) == 10


@pytest.mark.asyncio
async def test_registered_tool_names_match_product_surface() -> None:
    assert EXPECTED_TOOL_NAMES == (
        "get_user_story",
        "get_existing_test_cases",
        "search_similar_test_cases",
        "get_related_bugs",
        "analyze_requirement",
        "analyze_codebase",
        "detect_duplicate_test_cases",
        "generate_coverage_report",
        "create_test_cases",
        "link_test_cases",
    )


@pytest.mark.asyncio
async def test_get_user_story_returns_config_error_without_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ADO_ORGANIZATION", raising=False)
    monkeypatch.delenv("ADO_PROJECT", raising=False)
    monkeypatch.delenv("ADO_PAT", raising=False)
    from qa_intelligence.infrastructure.config import clear_settings_cache

    clear_settings_cache()
    reset_container()

    payload = await get_user_story_mod.get_user_story(73230)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "CONFIG_INVALID"


@pytest.mark.asyncio
async def test_get_user_story_uses_story_service(monkeypatch: pytest.MonkeyPatch) -> None:
    story = UserStory(
        id=73230,
        title="Order API",
        acceptance_criteria=[
            AcceptanceCriteria(order=1, text="Returns 200 for valid payload", id="AC-1")
        ],
    )
    fake_story_service = MagicMock()
    fake_story_service.get_user_story = AsyncMock(return_value=story)
    fake_container = MagicMock()
    fake_container.story_service = fake_story_service

    monkeypatch.setattr(
        "qa_intelligence.mcp.tools.get_user_story.get_container",
        lambda: fake_container,
    )

    payload = await get_user_story_mod.get_user_story(73230)
    assert payload["ok"] is True
    assert payload["data"]["id"] == 73230
    assert payload["data"]["title"] == "Order API"
    fake_story_service.get_user_story.assert_awaited_once_with(73230)


@pytest.mark.asyncio
async def test_get_user_story_maps_service_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_story_service = MagicMock()
    fake_story_service.get_user_story = AsyncMock(
        side_effect=ConfigurationError("missing credentials")
    )
    fake_container = MagicMock()
    fake_container.story_service = fake_story_service
    monkeypatch.setattr(
        "qa_intelligence.mcp.tools.get_user_story.get_container",
        lambda: fake_container,
    )

    payload = await get_user_story_mod.get_user_story(1)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "CONFIG_INVALID"


def _extract_payload(result: object) -> dict[str, Any]:
    if isinstance(result, ToolResponse):
        return result.model_dump()
    if isinstance(result, dict):
        return result
    data = getattr(result, "data", None)
    if isinstance(data, ToolResponse):
        return data.model_dump()
    if isinstance(data, dict):
        return data
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured
    content = getattr(result, "content", None)
    if content:
        import json

        first = content[0]
        text = getattr(first, "text", None)
        if text:
            return json.loads(text)
    raise AssertionError(f"Unexpected tool result shape: {type(result)!r} {result!r}")
