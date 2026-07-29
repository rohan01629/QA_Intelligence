"""Helpers to coerce MCP payloads into domain models."""

from __future__ import annotations

from typing import Any

from qa_intelligence.domain.models.bug import Bug
from qa_intelligence.domain.models.read_models import TestCaseSummary
from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.domain.models.user_story import UserStory


def parse_user_story(payload: dict[str, Any]) -> UserStory:
    return UserStory.model_validate(payload)


def parse_test_case_summary(payload: dict[str, Any], *, fallback_id: int) -> TestCaseSummary:
    data = dict(payload)
    if "id" not in data or data["id"] is None:
        data["id"] = fallback_id
    if "title" not in data or not data["title"]:
        data["title"] = f"Untitled-{fallback_id}"
    # Drafts may only have the three write fields.
    data.setdefault("steps", data.get("steps") or [])
    data.setdefault("expected_results", data.get("expected_results") or [])
    data.setdefault("state", data.get("state") or "Unknown")
    return TestCaseSummary.model_validate(data)


def parse_test_case_summaries(
    payloads: list[dict[str, Any]] | None,
    *,
    id_base: int = 900_000,
) -> list[TestCaseSummary]:
    if not payloads:
        return []
    results: list[TestCaseSummary] = []
    for index, payload in enumerate(payloads, start=1):
        results.append(parse_test_case_summary(payload, fallback_id=id_base + index))
    return results


def parse_bugs(payloads: list[dict[str, Any]] | None) -> list[Bug]:
    if not payloads:
        return []
    bugs: list[Bug] = []
    for index, payload in enumerate(payloads, start=1):
        data = dict(payload)
        data.setdefault("id", 800_000 + index)
        data.setdefault("title", f"Bug-{data['id']}")
        data.setdefault("state", "Active")
        bugs.append(Bug.model_validate(data))
    return bugs


def parse_test_cases(payloads: list[Any]) -> list[TestCase]:
    cases: list[TestCase] = []
    for item in payloads:
        if isinstance(item, TestCase):
            cases.append(item)
        else:
            cases.append(TestCase.model_validate(item))
    return cases
