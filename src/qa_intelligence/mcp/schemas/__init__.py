"""MCP request/response DTO schemas."""

from __future__ import annotations

from qa_intelligence.mcp.schemas.common import ErrorBody, ToolResponse
from qa_intelligence.mcp.schemas.requests import (
    AnalyzeRequirementRequest,
    CreateTestCasesRequest,
    DetectDuplicateTestCasesRequest,
    GenerateCoverageReportRequest,
    GetExistingTestCasesRequest,
    GetRelatedBugsRequest,
    GetUserStoryRequest,
    LinkTestCasesRequest,
    SearchSimilarTestCasesRequest,
)

__all__ = [
    "AnalyzeRequirementRequest",
    "CreateTestCasesRequest",
    "DetectDuplicateTestCasesRequest",
    "ErrorBody",
    "GenerateCoverageReportRequest",
    "GetExistingTestCasesRequest",
    "GetRelatedBugsRequest",
    "GetUserStoryRequest",
    "LinkTestCasesRequest",
    "SearchSimilarTestCasesRequest",
    "ToolResponse",
]
