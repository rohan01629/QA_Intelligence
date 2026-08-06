"""ADO create document includes Rule 13 IsRegression / Sanity toggles."""

from __future__ import annotations

from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.infrastructure.ado.mappers import build_test_case_create_document


def _field_map(document: list[dict[object, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for op in document:
        path = str(op.get("path") or "")
        if path.startswith("/fields/"):
            out[path[len("/fields/") :]] = op.get("value")
    return out


def test_create_document_sets_regression_toggle() -> None:
    case = TestCase(
        title="Verify adjacent workflow remains stable",
        steps=["Open reports", "Click WITSML"],
        expected_results=["Reports open", "Download still works"],
        is_regression=True,
    )
    fields = _field_map(build_test_case_create_document(case))
    assert fields["Custom.IsRegression"] is True
    assert fields["Custom.Sanity"] is False
    assert fields["System.Title"] == case.title


def test_create_document_sets_sanity_toggle_for_critical() -> None:
    case = TestCase(
        title="Verify unauthorized operator cannot invoke command",
        steps=["Sign in as Operator", "Attempt generate"],
        expected_results=["Signed in", "Command blocked"],
        is_sanity=True,
    )
    fields = _field_map(build_test_case_create_document(case))
    assert fields["Custom.IsRegression"] is False
    assert fields["Custom.Sanity"] is True


def test_create_document_standard_both_false() -> None:
    case = TestCase(
        title="Verify label text",
        steps=["Open screen"],
        expected_results=["Label visible"],
    )
    fields = _field_map(build_test_case_create_document(case))
    assert fields["Custom.IsRegression"] is False
    assert fields["Custom.Sanity"] is False


def test_create_document_respects_field_name_overrides() -> None:
    case = TestCase(
        title="Verify login",
        steps=["Open"],
        expected_results=["Ok"],
        is_regression=True,
    )
    fields = _field_map(
        build_test_case_create_document(
            case,
            is_regression_field="Custom.FooRegression",
            sanity_field="Custom.FooSanity",
        )
    )
    assert fields["Custom.FooRegression"] is True
    assert fields["Custom.FooSanity"] is False
    assert "Custom.IsRegression" not in fields
