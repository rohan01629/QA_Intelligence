"""Tests for Azure DevOps client, auth, mappers, and repositories."""

from __future__ import annotations

import base64

import httpx
import pytest

from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.infrastructure.ado.auth import PatAuthProvider
from qa_intelligence.infrastructure.ado.client import AzureDevOpsClient
from qa_intelligence.infrastructure.ado.mappers import (
    build_tcm_steps_xml,
    map_user_story,
    parse_tcm_steps,
)
from qa_intelligence.infrastructure.config import Settings
from qa_intelligence.infrastructure.errors import (
    AuthError,
    NotFoundError,
    RateLimitError,
    UpstreamError,
)
from qa_intelligence.repositories.user_story_repository import AdoUserStoryRepository


def _settings(**overrides: object) -> Settings:
    data: dict[str, object] = {
        "ado_organization": "contoso",
        "ado_project": "Demo",
        "ado_base_url": "https://dev.azure.com",
        "ado_api_version": "7.1",
        "ado_pat": "fake-pat-token",
        "http_timeout_seconds": 5.0,
        "http_max_retries": 2,
        "log_level": "ERROR",
    }
    data.update(overrides)
    return Settings.model_validate(data)


def test_pat_auth_provider_builds_basic_header() -> None:
    provider = PatAuthProvider("secret-pat")
    header = provider.get_authorization_header()
    expected = base64.b64encode(b":secret-pat").decode("ascii")
    assert header == {"Authorization": f"Basic {expected}"}


def test_pat_auth_rejects_blank() -> None:
    with pytest.raises(ValueError):
        PatAuthProvider("  ")


def test_tcm_steps_round_trip() -> None:
    case = TestCase(
        title="Verify login",
        steps=["Open login.", "Submit."],
        expected_results=["Login opens.", "User authenticated."],
    )
    xml = build_tcm_steps_xml(case)
    steps, expected = parse_tcm_steps(xml)
    assert steps == case.steps
    assert expected == case.expected_results


def test_map_user_story_parses_acceptance_criteria() -> None:
    payload = {
        "id": 73230,
        "fields": {
            "System.Title": "Backend API change",
            "System.Description": "<div>Desc</div>",
            "System.State": "Active",
            "System.AreaPath": "Demo\\API",
            "System.IterationPath": "Demo\\Sprint 1",
            "System.Tags": "api; backend",
            "Microsoft.VSTS.Common.AcceptanceCriteria": (
                "<div>1. Returns 200<br/>2. Returns 400</div>"
            ),
            "System.WorkItemType": "User Story",
        },
    }
    story = map_user_story(payload, _settings())
    assert story.id == 73230
    assert story.title == "Backend API change"
    assert len(story.acceptance_criteria) >= 1
    assert "api" in story.tags


@pytest.mark.asyncio
async def test_client_maps_404_to_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "missing"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = AzureDevOpsClient(_settings(), PatAuthProvider("pat"), http_client=http)
        with pytest.raises(NotFoundError):
            await client.get("/_apis/wit/workitems/1")


@pytest.mark.asyncio
async def test_client_maps_401_to_auth_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "Authorization" in request.headers
        return httpx.Response(401, json={"message": "bad auth"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = AzureDevOpsClient(_settings(), PatAuthProvider("pat"), http_client=http)
        with pytest.raises(AuthError):
            await client.get("/_apis/wit/workitems/1")


@pytest.mark.asyncio
async def test_client_retries_429_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, json={})
        return httpx.Response(200, json={"id": 1, "fields": {"System.Title": "OK"}})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = AzureDevOpsClient(
            _settings(http_max_retries=2),
            PatAuthProvider("pat"),
            http_client=http,
        )
        data = await client.get("/_apis/wit/workitems/1")
        assert data["id"] == 1
        assert calls["n"] == 2


@pytest.mark.asyncio
async def test_client_retries_5xx_then_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"message": "down"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = AzureDevOpsClient(
            _settings(http_max_retries=1),
            PatAuthProvider("pat"),
            http_client=http,
        )
        with pytest.raises(UpstreamError):
            await client.get("/_apis/wit/workitems/1")


@pytest.mark.asyncio
async def test_work_item_repository_get_user_story() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": 73230,
                "fields": {
                    "System.Title": "Story",
                    "System.Description": "Desc",
                    "System.State": "Active",
                    "System.AreaPath": "Demo",
                    "System.IterationPath": "Demo\\1",
                    "System.Tags": "",
                    "System.WorkItemType": "User Story",
                    "Microsoft.VSTS.Common.AcceptanceCriteria": "Must work",
                },
                "relations": [],
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = AzureDevOpsClient(_settings(), PatAuthProvider("pat"), http_client=http)
        repo = AdoUserStoryRepository(client)
        story = await repo.get_by_id(73230)
        assert story.id == 73230
        assert story.title == "Story"


@pytest.mark.asyncio
async def test_rate_limit_exhausted_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "0"}, json={})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = AzureDevOpsClient(
            _settings(http_max_retries=0),
            PatAuthProvider("pat"),
            http_client=http,
        )
        with pytest.raises(RateLimitError):
            await client.get("/_apis/wit/workitems/1")
