"""Domain entity and value-object models."""

from __future__ import annotations

from qa_intelligence.domain.models.analysis import (
    FeatureAnalysis,
    RequirementAnalysis,
    RequirementGap,
)
from qa_intelligence.domain.models.bug import Bug
from qa_intelligence.domain.models.code_intelligence import (
    AffectedApi,
    AffectedFile,
    CodeArtifactRole,
    CodeSignal,
    CodeSourceKind,
    ImplementationSummary,
)
from qa_intelligence.domain.models.coverage import CoverageReport, ScenarioRef
from qa_intelligence.domain.models.coverage_matrix import (
    AcceptanceCriterionMap,
    BugMapEntry,
    CoverageAnalysisResult,
    CoverageMatrixRow,
    CoverageStatus,
    TestCaseMapEntry,
)
from qa_intelligence.domain.models.detection import DuplicateDetectionResult, ScenarioMatch
from qa_intelligence.domain.models.duplicate import DuplicateAnalysis, DuplicateCluster
from qa_intelligence.domain.models.generation import (
    GeneratedTestCaseRecord,
    GenerationMode,
    TestCaseGenerationResult,
)
from qa_intelligence.domain.models.orchestration import (
    WorkflowExecutionSummary,
    WorkflowStepName,
    WorkflowStepResult,
    WorkflowStepStatus,
)
from qa_intelligence.domain.models.qa_strategy import (
    CategoryExclusion,
    CoverageEstimates,
    QAStrategy,
)
from qa_intelligence.domain.models.read_models import RelatedWorkItemRef, TestCaseSummary
from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.domain.models.test_strategy import (
    CategoryDecision,
    RiskBasedTestingStrategy,
    TestStrategy,
)
from qa_intelligence.domain.models.user_story import AcceptanceCriteria, UserStory
from qa_intelligence.domain.models.validation import ValidationIssue, ValidationResult
from qa_intelligence.domain.models.write_results import CreateResult, LinkResult

__all__ = [
    "AcceptanceCriteria",
    "AcceptanceCriterionMap",
    "AffectedApi",
    "AffectedFile",
    "Bug",
    "BugMapEntry",
    "CategoryDecision",
    "CategoryExclusion",
    "CodeArtifactRole",
    "CodeSignal",
    "CodeSourceKind",
    "CoverageAnalysisResult",
    "CoverageEstimates",
    "CoverageMatrixRow",
    "CoverageReport",
    "CoverageStatus",
    "CreateResult",
    "DuplicateAnalysis",
    "DuplicateCluster",
    "DuplicateDetectionResult",
    "FeatureAnalysis",
    "GeneratedTestCaseRecord",
    "GenerationMode",
    "ImplementationSummary",
    "LinkResult",
    "QAStrategy",
    "RelatedWorkItemRef",
    "RequirementAnalysis",
    "RequirementGap",
    "RiskBasedTestingStrategy",
    "ScenarioMatch",
    "ScenarioRef",
    "TestCase",
    "TestCaseGenerationResult",
    "TestCaseMapEntry",
    "TestCaseSummary",
    "TestStrategy",
    "UserStory",
    "ValidationIssue",
    "ValidationResult",
    "WorkflowExecutionSummary",
    "WorkflowStepName",
    "WorkflowStepResult",
    "WorkflowStepStatus",
]
