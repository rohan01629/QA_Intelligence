"""Unit tests for TestCase domain validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from qa_intelligence.domain.models import TestCase


def test_valid_test_case_with_matching_steps_and_expected_results() -> None:
    case = TestCase(
        title="Verify workflow with no tangent added",
        steps=[
            "Open Minifrac Analysis.",
            "Do not add any tangent.",
            "Execute the workflow.",
            "Monitor the network requests.",
        ],
        expected_results=[
            "Minifrac Analysis opens successfully.",
            "No tangent is present.",
            "Workflow executes successfully.",
            "No redundant GET request with X=0,Y=0 is sent.",
        ],
    )
    assert case.step_count == 4
    assert case.expected_result_count == 4
    assert case.step_count == case.expected_result_count


def test_rejects_step_count_not_equal_expected_result_count() -> None:
    with pytest.raises(ValidationError) as exc_info:
        TestCase(
            title="Verify login",
            steps=["Open login page.", "Enter credentials.", "Click submit."],
            expected_results=["Login page opens.", "Credentials accepted."],
        )
    assert "step_count must equal expected_result_count" in str(exc_info.value)


def test_rejects_blank_title() -> None:
    with pytest.raises(ValidationError):
        TestCase(
            title="   ",
            steps=["Do something."],
            expected_results=["Something happens."],
        )


def test_rejects_empty_steps() -> None:
    with pytest.raises(ValidationError):
        TestCase(
            title="Verify login",
            steps=[],
            expected_results=["Login succeeds."],
        )


def test_rejects_empty_expected_results() -> None:
    with pytest.raises(ValidationError):
        TestCase(
            title="Verify login",
            steps=["Open login page."],
            expected_results=[],
        )


def test_rejects_blank_step_entry() -> None:
    with pytest.raises(ValidationError):
        TestCase(
            title="Verify login",
            steps=["Open login page.", "  "],
            expected_results=["Login page opens.", "Ok."],
        )


def test_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        TestCase.model_validate(
            {
                "title": "Verify login",
                "steps": ["Open login page."],
                "expected_results": ["Login page opens."],
                "priority": "High",
            }
        )


def test_strips_whitespace_from_entries() -> None:
    case = TestCase(
        title="  Verify login  ",
        steps=["  Open login page.  "],
        expected_results=["  Login page opens.  "],
    )
    assert case.title == "Verify login"
    assert case.steps == ["Open login page."]
    assert case.expected_results == ["Login page opens."]
