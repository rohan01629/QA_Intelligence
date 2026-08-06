"""Azure DevOps Test Case repository — data access only."""

from __future__ import annotations

import structlog

from qa_intelligence.domain.models.read_models import TestCaseSummary
from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.infrastructure.ado.client import AzureDevOpsClient
from qa_intelligence.infrastructure.ado.mappers import (
    build_link_document,
    build_test_case_create_document,
    extract_related_ids,
    map_test_case_summary,
)
from qa_intelligence.infrastructure.errors import ConfigurationError

logger = structlog.get_logger(__name__)


def _escape_wiql(value: str) -> str:
    return value.replace("'", "''")


class AdoTestCaseRepository:
    """TestCaseRepository adapter backed by Azure DevOps WIT / Test APIs."""

    def __init__(self, client: AzureDevOpsClient) -> None:
        self._client = client

    async def get_by_id(self, test_case_id: int) -> TestCaseSummary:
        payload = await self._client.get_work_item(test_case_id, expand=None)
        summary = map_test_case_summary(payload)
        logger.info("ado.test_case_fetched", test_case_id=summary.id)
        return summary

    async def list_linked_to_story(self, user_story_id: int) -> list[TestCaseSummary]:
        story = await self._client.get_work_item(user_story_id, expand="relations")
        related = extract_related_ids(story)
        if not related:
            return []

        ids = [item_id for item_id, _ in related]
        link_by_id = {item_id: link for item_id, link in related}
        payloads = await self._client.get_work_items_batch(ids)

        test_case_type = self._client.settings.ado_test_case_type
        results: list[TestCaseSummary] = []
        for payload in payloads:
            fields = payload.get("fields") or {}
            if fields.get("System.WorkItemType") != test_case_type:
                continue
            wid = int(payload["id"])
            results.append(
                map_test_case_summary(payload, link_type=link_by_id.get(wid))
            )

        logger.info(
            "ado.linked_test_cases_fetched",
            user_story_id=user_story_id,
            count=len(results),
        )
        return results

    async def search(
        self,
        query: str,
        *,
        area_path: str | None = None,
        top: int = 25,
    ) -> list[TestCaseSummary]:
        top = max(1, min(top, 50))
        needle = _escape_wiql(query.strip())
        test_case_type = _escape_wiql(self._client.settings.ado_test_case_type)

        clauses = [
            f"[System.WorkItemType] = '{test_case_type}'",
            f"[System.Title] CONTAINS '{needle}'",
        ]
        if area_path:
            clauses.append(f"[System.AreaPath] UNDER '{_escape_wiql(area_path)}'")

        wiql = (
            "SELECT [System.Id] FROM WorkItems WHERE "
            + " AND ".join(clauses)
            + " ORDER BY [System.ChangedDate] DESC"
        )
        ids = (await self._client.query_wiql(wiql))[:top]
        if not ids:
            return []

        payloads = await self._client.get_work_items_batch(ids)
        results = [map_test_case_summary(payload) for payload in payloads]
        logger.info(
            "ado.test_case_search",
            query=query,
            area_path=area_path,
            count=len(results),
        )
        return results

    async def create(self, draft: TestCase) -> int:
        settings = self._client.settings
        document = build_test_case_create_document(
            draft,
            is_regression_field=settings.ado_is_regression_field,
            sanity_field=settings.ado_sanity_field,
        )
        created = await self._client.create_work_item(
            settings.ado_test_case_type,
            document,
        )
        test_case_id = int(created["id"])
        logger.info("ado.test_case_created", test_case_id=test_case_id)
        return test_case_id

    async def link_to_user_story(
        self,
        user_story_id: int,
        test_case_id: int,
    ) -> None:
        target_url = self._client.project_url(f"/_apis/wit/workItems/{user_story_id}")
        document = build_link_document(
            target_url=target_url,
            relation_type=self._client.settings.ado_tested_by_relation,
        )
        await self._client.update_work_item(test_case_id, document)
        logger.info(
            "ado.test_case_linked",
            user_story_id=user_story_id,
            test_case_id=test_case_id,
        )

    async def add_to_suite(self, suite_id: int, test_case_id: int) -> None:
        plan_id = self._client.settings.ado_default_test_plan_id
        if plan_id is None:
            raise ConfigurationError(
                "ADO_DEFAULT_TEST_PLAN_ID is required to add test cases to a suite",
                details={"suite_id": suite_id, "test_case_id": test_case_id},
            )
        await self._client.add_test_cases_to_suite(plan_id, suite_id, [test_case_id])
        logger.info(
            "ado.test_case_added_to_suite",
            plan_id=plan_id,
            suite_id=suite_id,
            test_case_id=test_case_id,
        )
