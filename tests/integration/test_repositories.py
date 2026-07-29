"""Repository integration tests — Azure DevOps data access only."""

from __future__ import annotations

import httpx
import pytest

from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.infrastructure.ado.auth import PatAuthProvider
from qa_intelligence.infrastructure.ado.client import AzureDevOpsClient
from qa_intelligence.infrastructure.config import Settings
from qa_intelligence.repositories.bug_repository import AdoBugRepository
from qa_intelligence.repositories.test_case_repository import AdoTestCaseRepository
from qa_intelligence.repositories.user_story_repository import AdoUserStoryRepository


def _settings() -> Settings:
    return Settings.model_validate(
        {
            "ado_organization": "contoso",
            "ado_project": "Demo",
            "ado_base_url": "https://dev.azure.com",
            "ado_api_version": "7.1",
            "ado_pat": "fake-pat-token",
            "http_timeout_seconds": 5.0,
            "http_max_retries": 0,
            "log_level": "ERROR",
        }
    )


@pytest.mark.asyncio
async def test_test_case_repository_search_and_create() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        calls.append(f"{request.method} {path}")
        if path.endswith("/_apis/wit/wiql"):
            return httpx.Response(200, json={"workItems": [{"id": 101}]})
        if path.endswith("/_apis/wit/workitemsbatch"):
            return httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "id": 101,
                            "fields": {
                                "System.Title": "Verify API success",
                                "System.State": "Design",
                                "System.WorkItemType": "Test Case",
                                "Microsoft.VSTS.TCM.Steps": (
                                    '<steps id="0" last="1">'
                                    '<step id="1" type="ActionStep">'
                                    '<parameterizedString isformatted="true">Call API</parameterizedString>'
                                    '<parameterizedString isformatted="true">200 OK</parameterizedString>'
                                    "<description/></step></steps>"
                                ),
                            },
                        }
                    ]
                },
            )
        if "/_apis/wit/workitems/$Test%20Case" in path or path.endswith(
            "/_apis/wit/workitems/$Test Case"
        ):
            return httpx.Response(200, json={"id": 202})
        # create uses URL-encoded type
        if "workitems/$" in path and request.method == "POST":
            return httpx.Response(200, json={"id": 202})
        return httpx.Response(404, json={"message": path})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = AzureDevOpsClient(_settings(), PatAuthProvider("pat"), http_client=http)
        repo = AdoTestCaseRepository(client)

        found = await repo.search("API", top=10)
        assert len(found) == 1
        assert found[0].id == 101
        assert found[0].steps == ["Call API"]

        created_id = await repo.create(
            TestCase(
                title="Verify create",
                steps=["Do it"],
                expected_results=["Done"],
            )
        )
        assert created_id == 202


@pytest.mark.asyncio
async def test_bug_repository_list_related_to_story() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/workitems/73230"):
            return httpx.Response(
                200,
                json={
                    "id": 73230,
                    "fields": {
                        "System.Title": "Story",
                        "System.AreaPath": "Demo\\API",
                        "System.WorkItemType": "User Story",
                    },
                    "relations": [
                        {
                            "rel": "System.LinkTypes.Related",
                            "url": "https://dev.azure.com/contoso/Demo/_apis/wit/workItems/55",
                        }
                    ],
                },
            )
        if path.endswith("/workitemsbatch"):
            return httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "id": 55,
                            "fields": {
                                "System.Title": "Null ref",
                                "System.State": "Active",
                                "System.WorkItemType": "Bug",
                            },
                        }
                    ]
                },
            )
        if path.endswith("/wiql"):
            return httpx.Response(200, json={"workItems": []})
        return httpx.Response(404, json={"message": path})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = AzureDevOpsClient(_settings(), PatAuthProvider("pat"), http_client=http)
        repo = AdoBugRepository(client)
        bugs = await repo.list_related_to_story(73230)
        assert len(bugs) == 1
        assert bugs[0].id == 55
        assert bugs[0].title == "Null ref"


@pytest.mark.asyncio
async def test_user_story_repository_related_refs() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": 1,
                "fields": {"System.Title": "S", "System.State": "Active"},
                "relations": [
                    {
                        "rel": "System.LinkTypes.Related",
                        "url": "https://dev.azure.com/contoso/Demo/_apis/wit/workItems/9",
                    }
                ],
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = AzureDevOpsClient(_settings(), PatAuthProvider("pat"), http_client=http)
        repo = AdoUserStoryRepository(client)
        refs = await repo.get_related_work_items(1)
        assert len(refs) == 1
        assert refs[0].id == 9
