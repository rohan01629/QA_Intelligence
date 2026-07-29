"""MCP tool request schemas (interface contracts)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from qa_intelligence.domain.models.test_case import TestCase


class GetUserStoryRequest(BaseModel):
    work_item_id: int = Field(..., gt=0, description="Azure DevOps user story work item ID")


class GetExistingTestCasesRequest(BaseModel):
    user_story_id: int = Field(..., gt=0)


class SearchSimilarTestCasesRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search text from title/AC/modules")
    area_path: str | None = Field(default=None, description="Optional Area Path scope")
    top: int = Field(default=25, ge=1, le=50)


class GetRelatedBugsRequest(BaseModel):
    user_story_id: int = Field(..., gt=0)


class AnalyzeRequirementRequest(BaseModel):
    user_story_id: int | None = Field(
        default=None,
        gt=0,
        description="User story ID to fetch and analyze",
    )
    user_story: dict[str, Any] | None = Field(
        default=None,
        description="Optional embedded UserStory payload instead of fetching by ID",
    )


class DetectDuplicateTestCasesRequest(BaseModel):
    candidates: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Candidate drafts or summaries",
    )
    existing: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Existing inventory / similar test cases",
    )


class GenerateCoverageReportRequest(BaseModel):
    user_story_id: int = Field(..., gt=0)
    requirement_analysis: dict[str, Any] | None = None
    existing_test_cases: list[dict[str, Any]] = Field(default_factory=list)
    similar_test_cases: list[dict[str, Any]] = Field(default_factory=list)
    related_bugs: list[dict[str, Any]] = Field(default_factory=list)
    drafts: list[dict[str, Any]] = Field(default_factory=list)


class CreateTestCasesRequest(BaseModel):
    test_cases: list[TestCase] = Field(
        ...,
        min_length=1,
        description="Test cases with only title, steps, expected_results",
    )
    dry_run: bool = False
    reject_duplicates: bool = True
    override_requirement_block: bool = False


class LinkTestCasesRequest(BaseModel):
    user_story_id: int = Field(..., gt=0)
    test_case_ids: list[int] = Field(..., min_length=1)
    dry_run: bool = False
