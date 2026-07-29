"""Thin MCP tool adapters (one module per tool)."""

from __future__ import annotations

from qa_intelligence.mcp.tools import (
    analyze_requirement as analyze_requirement_mod,
    create_test_cases as create_test_cases_mod,
    detect_duplicate_test_cases as detect_duplicate_test_cases_mod,
    generate_coverage_report as generate_coverage_report_mod,
    get_existing_test_cases as get_existing_test_cases_mod,
    get_related_bugs as get_related_bugs_mod,
    get_user_story as get_user_story_mod,
    link_test_cases as link_test_cases_mod,
    search_similar_test_cases as search_similar_test_cases_mod,
)

# Canonical ordered tool surface (closed set of 9).
TOOL_HANDLERS = (
    get_user_story_mod.get_user_story,
    get_existing_test_cases_mod.get_existing_test_cases,
    search_similar_test_cases_mod.search_similar_test_cases,
    get_related_bugs_mod.get_related_bugs,
    analyze_requirement_mod.analyze_requirement,
    detect_duplicate_test_cases_mod.detect_duplicate_test_cases,
    generate_coverage_report_mod.generate_coverage_report,
    create_test_cases_mod.create_test_cases,
    link_test_cases_mod.link_test_cases,
)

EXPECTED_TOOL_NAMES = tuple(handler.__name__ for handler in TOOL_HANDLERS)

__all__ = [
    "EXPECTED_TOOL_NAMES",
    "TOOL_HANDLERS",
]
