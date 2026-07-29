"""Orchestration workflow execution summary models."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import Field

from qa_intelligence.domain.enums import GenerationDirective
from qa_intelligence.domain.models.analysis import RequirementAnalysis
from qa_intelligence.domain.models.base import DomainModel
from qa_intelligence.domain.models.bug import Bug
from qa_intelligence.domain.models.coverage_matrix import CoverageAnalysisResult
from qa_intelligence.domain.models.detection import DuplicateDetectionResult
from qa_intelligence.domain.models.generation import TestCaseGenerationResult
from qa_intelligence.domain.models.read_models import TestCaseSummary
from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.domain.models.test_strategy import TestStrategy
from qa_intelligence.domain.models.user_story import UserStory
from qa_intelligence.domain.models.write_results import CreateResult, LinkResult


class WorkflowStepName(StrEnum):
    """Ordered steps in the end-to-end QA workflow."""

    FETCH_USER_STORY = "fetch_user_story"
    ANALYZE_REQUIREMENT = "analyze_requirement"
    FETCH_EXISTING_TEST_CASES = "fetch_existing_test_cases"
    FETCH_BUGS = "fetch_bugs"
    DUPLICATE_DETECTION = "duplicate_detection"
    COVERAGE_ANALYSIS = "coverage_analysis"
    TEST_STRATEGY = "test_strategy"
    GENERATE_TEST_CASES = "generate_test_cases"
    VALIDATE_TEST_CASES = "validate_test_cases"
    PUBLISH_TO_AZURE_DEVOPS = "publish_to_azure_devops"
    LINK_TEST_CASES = "link_test_cases"


class WorkflowStepStatus(StrEnum):
    SUCCEEDED = "succeeded"
    SKIPPED = "skipped"
    FAILED = "failed"
    BLOCKED = "blocked"


class WorkflowStepResult(DomainModel):
    """Outcome of a single orchestration step."""

    name: WorkflowStepName
    status: WorkflowStepStatus
    message: str = ""
    details: dict[str, object] = Field(default_factory=dict)


class WorkflowExecutionSummary(DomainModel):
    """Complete execution summary for the orchestration workflow."""

    __test__ = False

    user_story_id: Annotated[int, Field(gt=0)]
    ok: bool
    dry_run: bool = False
    blocked: bool = False
    generation_directive: GenerationDirective | None = None
    steps: list[WorkflowStepResult] = Field(default_factory=list)

    user_story: UserStory | None = None
    requirement_analysis: RequirementAnalysis | None = None
    existing_test_cases: list[TestCaseSummary] = Field(default_factory=list)
    related_bugs: list[Bug] = Field(default_factory=list)
    duplicate_detection: DuplicateDetectionResult | None = None
    coverage_analysis: CoverageAnalysisResult | None = None
    test_strategy: TestStrategy | None = None
    generation: TestCaseGenerationResult | None = None
    validated_test_cases: list[TestCase] = Field(default_factory=list)
    create_results: list[CreateResult] = Field(default_factory=list)
    link_results: list[LinkResult] = Field(default_factory=list)

    created_ids: list[int] = Field(default_factory=list)
    linked_ids: list[int] = Field(default_factory=list)
    rejected_count: Annotated[int, Field(ge=0)] = 0
    notes: str = ""
