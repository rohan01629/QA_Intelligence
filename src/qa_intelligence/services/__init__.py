"""Application service layer."""

from __future__ import annotations

from qa_intelligence.services.bug_service import BugService
from qa_intelligence.services.code_intelligence_service import CodeIntelligenceService
from qa_intelligence.services.coverage_analysis_service import CoverageAnalysisService
from qa_intelligence.services.duplicate_detection_service import DuplicateDetectionService
from qa_intelligence.services.impact_analysis_service import ImpactAnalysisService
from qa_intelligence.services.implementation_summary_builder import ImplementationSummaryBuilder
from qa_intelligence.services.linking_service import LinkingService
from qa_intelligence.services.orchestration_service import OrchestrationService
from qa_intelligence.services.repository_search_service import RepositorySearchService
from qa_intelligence.services.requirement_analysis_service import RequirementAnalysisService
from qa_intelligence.services.story_service import StoryService
from qa_intelligence.services.test_case_generation_service import TestCaseGenerationService
from qa_intelligence.services.test_case_service import TestCaseService
from qa_intelligence.services.test_strategy_service import TestStrategyService

# Backward-compatible aliases used in architecture docs.
AnalysisService = RequirementAnalysisService
DuplicateService = DuplicateDetectionService
CoverageService = CoverageAnalysisService

__all__ = [
    "AnalysisService",
    "BugService",
    "CodeIntelligenceService",
    "CoverageAnalysisService",
    "CoverageService",
    "DuplicateDetectionService",
    "DuplicateService",
    "ImpactAnalysisService",
    "ImplementationSummaryBuilder",
    "LinkingService",
    "OrchestrationService",
    "RepositorySearchService",
    "RequirementAnalysisService",
    "StoryService",
    "TestCaseGenerationService",
    "TestCaseService",
    "TestStrategyService",
]
