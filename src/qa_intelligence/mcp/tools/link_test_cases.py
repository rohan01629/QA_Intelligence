"""MCP tool: link_test_cases."""

from __future__ import annotations

from qa_intelligence.mcp import responses
from qa_intelligence.mcp.runtime import get_container


async def link_test_cases(
    user_story_id: int,
    test_case_ids: list[int],
    dry_run: bool = True,
) -> dict[str, object]:
    """Link created Test Cases to a User Story in Azure DevOps.

    Defaults to dry_run=true (no ADO writes). Real links require
    ADO_WRITES_ENABLED=true and dry_run=false after explicit user approval.
    """
    try:
        from qa_intelligence.infrastructure.safety import ensure_ado_writes_allowed

        container = get_container()
        ensure_ado_writes_allowed(
            container.settings,
            dry_run=dry_run,
            action="link_test_cases",
        )
        results = await container.linking_service.link(
            user_story_id,
            test_case_ids,
            dry_run=dry_run,
        )
        return responses.success(results).model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        return responses.from_exception(exc, tool_name="link_test_cases").model_dump(mode="json")
