"""MCP tool: detect_duplicate_test_cases."""

from __future__ import annotations

from typing import Any

from qa_intelligence.mcp import responses
from qa_intelligence.mcp.parsers import parse_test_case_summaries
from qa_intelligence.mcp.runtime import get_container


async def detect_duplicate_test_cases(
    candidates: list[dict[str, Any]] | None = None,
    existing: list[dict[str, Any]] | None = None,
) -> dict[str, object]:
    """Detect semantic duplicate test scenarios between candidates and existing cases."""
    try:
        container = get_container()
        candidate_summaries = parse_test_case_summaries(candidates, id_base=700_000)
        existing_summaries = parse_test_case_summaries(existing, id_base=710_000)
        analysis = container.duplicate_detection_service.detect_duplicate_clusters(
            candidate_summaries,
            existing_summaries,
        )
        return responses.success(analysis.clusters).model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        return responses.from_exception(exc, tool_name="detect_duplicate_test_cases").model_dump(
            mode="json"
        )
