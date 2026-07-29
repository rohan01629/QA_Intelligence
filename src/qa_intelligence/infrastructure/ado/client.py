"""Async Azure DevOps REST client with retries, logging, and error mapping."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Mapping
from typing import Any
from urllib.parse import quote

import httpx
import structlog

from qa_intelligence.infrastructure.ado.auth import AuthProvider
from qa_intelligence.infrastructure.config import Settings
from qa_intelligence.infrastructure.errors import (
    AuthError,
    NotFoundError,
    RateLimitError,
    UpstreamError,
    WriteError,
)

logger = structlog.get_logger(__name__)


class AzureDevOpsClient:
    """Reusable async HTTP client for Azure DevOps REST APIs."""

    def __init__(
        self,
        settings: Settings,
        auth_provider: AuthProvider,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._auth_provider = auth_provider
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(settings.http_timeout_seconds),
            headers={"Accept": "application/json"},
        )

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def api_version(self) -> str:
        return self._settings.ado_api_version

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AzureDevOpsClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def project_url(self, path: str) -> str:
        """Build an absolute project-scoped URL (path may start with /)."""
        base = self._settings.ado_project_base
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{base}{path}"

    def org_url(self, path: str) -> str:
        base = self._settings.ado_org_base
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{base}{path}"

    async def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        project_scoped: bool = True,
    ) -> Any:
        return await self.request(
            "GET",
            path,
            params=params,
            project_scoped=project_scoped,
        )

    async def post(
        self,
        path: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
        project_scoped: bool = True,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self.request(
            "POST",
            path,
            json=json,
            params=params,
            project_scoped=project_scoped,
            headers=headers,
        )

    async def patch(
        self,
        path: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
        project_scoped: bool = True,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self.request(
            "PATCH",
            path,
            json=json,
            params=params,
            project_scoped=project_scoped,
            headers=headers,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        project_scoped: bool = True,
        headers: Mapping[str, str] | None = None,
        retry_writes: bool = False,
    ) -> Any:
        """Execute an HTTP request with retry on 429 / 5xx / transport errors."""
        url = self.project_url(path) if project_scoped else self.org_url(path)
        query = dict(params or {})
        query.setdefault("api-version", self.api_version)

        auth_headers = self._auth_provider.get_authorization_header()
        merged_headers = {**auth_headers, **(headers or {})}

        max_attempts = self._settings.http_max_retries + 1
        is_idempotent = method.upper() in {"GET", "HEAD", "OPTIONS"} or retry_writes

        last_error: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            started = asyncio.get_running_loop().time()
            try:
                response = await self._client.request(
                    method,
                    url,
                    params=query,
                    json=json,
                    headers=merged_headers,
                )
            except httpx.TimeoutException as exc:
                last_error = UpstreamError(
                    "Azure DevOps request timed out",
                    details={"method": method, "path": path, "attempt": attempt},
                )
                logger.warning(
                    "ado.request_timeout",
                    method=method,
                    path=path,
                    attempt=attempt,
                )
                if not is_idempotent or attempt >= max_attempts:
                    raise last_error from exc
                await self._sleep_backoff(attempt, retry_after=None)
                continue
            except httpx.HTTPError as exc:
                last_error = UpstreamError(
                    "Azure DevOps transport error",
                    details={"method": method, "path": path, "attempt": attempt},
                )
                logger.warning(
                    "ado.request_transport_error",
                    method=method,
                    path=path,
                    attempt=attempt,
                    error_type=type(exc).__name__,
                )
                if not is_idempotent or attempt >= max_attempts:
                    raise last_error from exc
                await self._sleep_backoff(attempt, retry_after=None)
                continue

            duration_ms = int((asyncio.get_running_loop().time() - started) * 1000)
            logger.info(
                "ado.request",
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                attempt=attempt,
            )

            if response.status_code in {401, 403}:
                raise AuthError(
                    "Azure DevOps authentication failed",
                    details={"status_code": response.status_code, "path": path},
                )

            if response.status_code == 404:
                raise NotFoundError(
                    "Azure DevOps resource not found",
                    details={"status_code": 404, "path": path},
                )

            if response.status_code == 429:
                retry_after = _parse_retry_after(response.headers.get("Retry-After"))
                error = RateLimitError(
                    "Azure DevOps rate limit exceeded",
                    retry_after_seconds=retry_after,
                    details={"path": path, "attempt": attempt},
                )
                if not is_idempotent or attempt >= max_attempts:
                    raise error
                await self._sleep_backoff(attempt, retry_after=retry_after)
                last_error = error
                continue

            if response.status_code >= 500:
                error = UpstreamError(
                    "Azure DevOps upstream error",
                    details={
                        "status_code": response.status_code,
                        "path": path,
                        "attempt": attempt,
                    },
                )
                if not is_idempotent or attempt >= max_attempts:
                    raise error
                await self._sleep_backoff(attempt, retry_after=None)
                last_error = error
                continue

            if response.status_code >= 400:
                # Non-retryable client error (e.g. 400 on write).
                message = "Azure DevOps request failed"
                details: dict[str, Any] = {
                    "status_code": response.status_code,
                    "path": path,
                }
                try:
                    body = response.json()
                    if isinstance(body, dict) and "message" in body:
                        details["ado_message"] = body["message"]
                except ValueError:
                    pass
                if method.upper() in {"POST", "PATCH", "PUT"}:
                    raise WriteError(message, details=details)
                raise UpstreamError(message, details=details)

            if response.status_code == 204 or not response.content:
                return None
            try:
                return response.json()
            except ValueError as exc:
                raise UpstreamError(
                    "Azure DevOps returned non-JSON response",
                    details={"path": path, "status_code": response.status_code},
                ) from exc

        assert last_error is not None
        raise last_error

    async def get_work_item(
        self,
        work_item_id: int,
        *,
        expand: str | None = "relations",
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if expand:
            params["$expand"] = expand
        data = await self.get(f"/_apis/wit/workitems/{work_item_id}", params=params)
        if not isinstance(data, dict):
            raise UpstreamError("Unexpected work item payload")
        return data

    async def get_work_items_batch(self, ids: list[int]) -> list[dict[str, Any]]:
        if not ids:
            return []
        payload = {
            "ids": ids,
            "fields": [
                "System.Id",
                "System.Title",
                "System.State",
                "System.WorkItemType",
                "System.AreaPath",
                "System.IterationPath",
                "System.Tags",
                "System.Description",
                "Microsoft.VSTS.TCM.Steps",
                "Microsoft.VSTS.TCM.ReproSteps",
                "Microsoft.VSTS.Common.Severity",
                "Microsoft.VSTS.Common.AcceptanceCriteria",
            ],
            "errorPolicy": "omit",
        }
        data = await self.post("/_apis/wit/workitemsbatch", json=payload)
        if not isinstance(data, dict):
            return []
        values = data.get("value", [])
        return [item for item in values if isinstance(item, dict)]

    async def query_wiql(self, wiql: str) -> list[int]:
        data = await self.post("/_apis/wit/wiql", json={"query": wiql})
        if not isinstance(data, dict):
            return []
        work_items = data.get("workItems", [])
        ids: list[int] = []
        for item in work_items:
            if isinstance(item, dict) and "id" in item:
                ids.append(int(item["id"]))
        return ids

    async def create_work_item(
        self,
        work_item_type: str,
        document: list[dict[str, Any]],
    ) -> dict[str, Any]:
        encoded_type = quote(work_item_type, safe="")
        data = await self.post(
            f"/_apis/wit/workitems/${encoded_type}",
            json=document,
            headers={"Content-Type": "application/json-patch+json"},
        )
        if not isinstance(data, dict) or "id" not in data:
            raise WriteError(
                "Azure DevOps create work item returned unexpected payload",
                details={"work_item_type": work_item_type},
            )
        return data

    async def update_work_item(
        self,
        work_item_id: int,
        document: list[dict[str, Any]],
    ) -> dict[str, Any]:
        data = await self.patch(
            f"/_apis/wit/workitems/{work_item_id}",
            json=document,
            headers={"Content-Type": "application/json-patch+json"},
        )
        if not isinstance(data, dict):
            raise WriteError(
                "Azure DevOps update work item returned unexpected payload",
                details={"work_item_id": work_item_id},
            )
        return data

    async def add_test_cases_to_suite(
        self,
        plan_id: int,
        suite_id: int,
        test_case_ids: list[int],
    ) -> Any:
        """Add test cases to a suite using the classic Test Management API."""
        if not test_case_ids:
            return None
        ids = ",".join(str(i) for i in test_case_ids)
        return await self.post(
            f"/_apis/test/Plans/{plan_id}/suites/{suite_id}/testcases/{ids}",
            json=None,
        )

    async def _sleep_backoff(
        self,
        attempt: int,
        *,
        retry_after: float | None,
    ) -> None:
        if retry_after is not None and retry_after > 0:
            delay = retry_after
        else:
            base = min(2 ** (attempt - 1), 8)
            delay = base + random.uniform(0, 0.25)
        logger.info("ado.retry_backoff", attempt=attempt, delay_seconds=round(delay, 3))
        await asyncio.sleep(delay)


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None
