"""Azure DevOps JSON ↔ domain model mappers."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from typing import Any
from xml.sax.saxutils import escape

from qa_intelligence.domain.models.bug import Bug
from qa_intelligence.domain.models.read_models import RelatedWorkItemRef, TestCaseSummary
from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.domain.models.user_story import AcceptanceCriteria, UserStory
from qa_intelligence.infrastructure.config import Settings

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_AC_HEADER_RE = re.compile(
    r"(?:acceptance\s*criteria|ac)\s*:?\s*",
    re.IGNORECASE,
)


def _fields(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("fields") or {}
    return raw if isinstance(raw, dict) else {}


def _as_str(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def strip_html(value: str) -> str:
    """Remove simple HTML tags and unescape entities."""
    text = _HTML_TAG_RE.sub(" ", value)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_tags(raw: object) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(tag).strip() for tag in raw if str(tag).strip()]
    return [part.strip() for part in str(raw).split(";") if part.strip()]


def parse_acceptance_criteria(raw: object) -> list[AcceptanceCriteria]:
    """Parse AC field / HTML into ordered AcceptanceCriteria entries."""
    if raw is None:
        return []
    text = strip_html(str(raw))
    if not text:
        return []

    text = _AC_HEADER_RE.sub("", text, count=1).strip()

    lines: list[str] = []
    for chunk in re.split(r"[\r\n]+", text):
        piece = chunk.strip(" \t-•*")
        piece = re.sub(r"^\d+[.)]\s*", "", piece).strip()
        if piece:
            lines.append(piece)

    if not lines and text:
        lines = [text]

    return [
        AcceptanceCriteria(order=index, text=line, id=f"AC-{index}")
        for index, line in enumerate(lines, start=1)
    ]


def parse_tcm_steps(raw: object) -> tuple[list[str], list[str]]:
    """Parse Microsoft.VSTS.TCM.Steps XML into parallel step/expected arrays."""
    if not raw:
        return [], []
    xml_text = str(raw).strip()
    if not xml_text:
        return [], []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return [], []

    steps: list[str] = []
    expected: list[str] = []
    for step_node in root.findall("step"):
        strings = step_node.findall("parameterizedString")
        action = strip_html(strings[0].text or "") if len(strings) > 0 else ""
        result = strip_html(strings[1].text or "") if len(strings) > 1 else ""
        if action or result:
            steps.append(action or "(empty step)")
            expected.append(result or "(empty expected result)")
    return steps, expected


def build_tcm_steps_xml(test_case: TestCase) -> str:
    """Build TCM Steps XML preserving 1:1 step ↔ expected pairing."""
    parts = [f'<steps id="0" last="{len(test_case.steps)}">']
    for index, (action, result) in enumerate(
        zip(test_case.steps, test_case.expected_results, strict=True),
        start=1,
    ):
        parts.append(
            f'<step id="{index}" type="ActionStep">'
            f'<parameterizedString isformatted="true">{escape(action)}</parameterizedString>'
            f'<parameterizedString isformatted="true">{escape(result)}</parameterizedString>'
            f"<description/>"
            f"</step>"
        )
    parts.append("</steps>")
    return "".join(parts)


def map_user_story(payload: dict[str, Any], settings: Settings) -> UserStory:
    fields = _fields(payload)
    ac_field = settings.ado_ac_field or "Microsoft.VSTS.Common.AcceptanceCriteria"
    ac_raw = fields.get(ac_field) or fields.get("System.Description")

    return UserStory(
        id=int(payload["id"]),
        title=_as_str(fields.get("System.Title"), "Untitled"),
        description=strip_html(_as_str(fields.get("System.Description"))),
        acceptance_criteria=parse_acceptance_criteria(ac_raw),
        state=_as_str(fields.get("System.State"), "Unknown"),
        area_path=_as_str(fields.get("System.AreaPath")),
        iteration_path=_as_str(fields.get("System.IterationPath")),
        tags=parse_tags(fields.get("System.Tags")),
    )


def map_bug(payload: dict[str, Any]) -> Bug:
    fields = _fields(payload)
    repro = strip_html(_as_str(fields.get("Microsoft.VSTS.TCM.ReproSteps")))
    return Bug(
        id=int(payload["id"]),
        title=_as_str(fields.get("System.Title"), "Untitled"),
        state=_as_str(fields.get("System.State"), "Unknown"),
        severity=_optional_str(fields.get("Microsoft.VSTS.Common.Severity")),
        repro_steps=repro or None,
        area_path=_optional_str(fields.get("System.AreaPath")),
        tags=parse_tags(fields.get("System.Tags")),
    )


def map_test_case_summary(
    payload: dict[str, Any],
    *,
    link_type: str | None = None,
) -> TestCaseSummary:
    fields = _fields(payload)
    steps, expected = parse_tcm_steps(fields.get("Microsoft.VSTS.TCM.Steps"))
    return TestCaseSummary(
        id=int(payload["id"]),
        title=_as_str(fields.get("System.Title"), "Untitled"),
        steps=steps,
        expected_results=expected,
        state=_as_str(fields.get("System.State"), "Unknown"),
        link_type=link_type,
        area_path=_optional_str(fields.get("System.AreaPath")),
    )


def map_related_refs(payload: dict[str, Any]) -> list[RelatedWorkItemRef]:
    relations = payload.get("relations") or []
    if not isinstance(relations, list):
        return []

    refs: list[RelatedWorkItemRef] = []
    for relation in relations:
        if not isinstance(relation, dict):
            continue
        rel = str(relation.get("rel") or "")
        url = str(relation.get("url") or "")
        match = re.search(r"/workItems/(\d+)$", url, re.IGNORECASE)
        if not match or not rel:
            continue
        refs.append(
            RelatedWorkItemRef(
                id=int(match.group(1)),
                link_type=rel,
                url=url or None,
            )
        )
    return refs


def extract_related_ids(
    payload: dict[str, Any],
    *,
    link_types: list[str] | None = None,
) -> list[tuple[int, str]]:
    """Return (related_id, rel_type) from work item relations."""
    allowed = set(link_types) if link_types else None
    results: list[tuple[int, str]] = []
    for ref in map_related_refs(payload):
        if allowed is not None and ref.link_type not in allowed:
            continue
        results.append((ref.id, ref.link_type))
    return results


def build_test_case_create_document(test_case: TestCase) -> list[dict[str, Any]]:
    """JSON Patch document for creating a Test Case work item."""
    return [
        {"op": "add", "path": "/fields/System.Title", "value": test_case.title},
        {
            "op": "add",
            "path": "/fields/Microsoft.VSTS.TCM.Steps",
            "value": build_tcm_steps_xml(test_case),
        },
    ]


def build_link_document(
    *,
    target_url: str,
    relation_type: str,
) -> list[dict[str, Any]]:
    return [
        {
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": relation_type,
                "url": target_url,
                "attributes": {"comment": "Linked by QA Intelligence MCP"},
            },
        }
    ]
