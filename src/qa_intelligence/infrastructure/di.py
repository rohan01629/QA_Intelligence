"""Dependency injection container for infrastructure and repositories."""

from __future__ import annotations

from dataclasses import dataclass

from qa_intelligence.infrastructure.ado.auth import AuthProvider, PatAuthProvider
from qa_intelligence.infrastructure.ado.client import AzureDevOpsClient
from qa_intelligence.infrastructure.config import Settings, get_settings
from qa_intelligence.infrastructure.logging import configure_logging
from qa_intelligence.repositories.bug_repository import AdoBugRepository
from qa_intelligence.repositories.protocols import (
    BugRepository,
    TestCaseRepository,
    UserStoryRepository,
)
from qa_intelligence.repositories.test_case_repository import AdoTestCaseRepository
from qa_intelligence.repositories.user_story_repository import AdoUserStoryRepository
from qa_intelligence.services.bug_service import BugService
from qa_intelligence.services.coverage_analysis_service import CoverageAnalysisService
from qa_intelligence.services.duplicate_detection_service import DuplicateDetectionService
from qa_intelligence.services.linking_service import LinkingService
from qa_intelligence.services.orchestration_service import OrchestrationService
from qa_intelligence.services.requirement_analysis_service import RequirementAnalysisService
from qa_intelligence.services.story_service import StoryService
from qa_intelligence.services.test_case_generation_service import TestCaseGenerationService
from qa_intelligence.services.test_case_service import TestCaseService
from qa_intelligence.services.test_strategy_service import TestStrategyService


@dataclass
class Container:
    """Composition root holding shared infrastructure and repositories."""

    settings: Settings
    auth_provider: AuthProvider
    ado_client: AzureDevOpsClient
    user_story_repository: UserStoryRepository
    test_case_repository: TestCaseRepository
    bug_repository: BugRepository
    story_service: StoryService
    bug_service: BugService
    test_case_service: TestCaseService
    linking_service: LinkingService
    requirement_analysis_service: RequirementAnalysisService
    duplicate_detection_service: DuplicateDetectionService
    coverage_analysis_service: CoverageAnalysisService
    test_strategy_service: TestStrategyService
    test_case_generation_service: TestCaseGenerationService
    orchestration_service: OrchestrationService

    async def aclose(self) -> None:
        await self.ado_client.aclose()


def build_container(settings: Settings | None = None) -> Container:
    """Wire settings, auth, ADO client, repositories, and application services."""
    resolved = settings or get_settings()
    configure_logging(resolved.log_level)

    auth_provider: AuthProvider = PatAuthProvider(resolved.ado_pat)
    ado_client = AzureDevOpsClient(resolved, auth_provider)
    user_story_repository: UserStoryRepository = AdoUserStoryRepository(ado_client)
    test_case_repository: TestCaseRepository = AdoTestCaseRepository(ado_client)
    bug_repository: BugRepository = AdoBugRepository(ado_client)

    story_service = StoryService(user_story_repository)
    bug_service = BugService(bug_repository)
    test_case_service = TestCaseService(test_case_repository)
    linking_service = LinkingService(test_case_repository)
    requirement_analysis_service = RequirementAnalysisService(user_story_repository)
    duplicate_detection_service = DuplicateDetectionService(
        duplicate_threshold=resolved.duplicate_threshold,
    )
    coverage_analysis_service = CoverageAnalysisService()
    test_strategy_service = TestStrategyService()
    test_case_generation_service = TestCaseGenerationService()
    orchestration_service = OrchestrationService(
        story_service=story_service,
        requirement_analysis_service=requirement_analysis_service,
        test_case_service=test_case_service,
        bug_service=bug_service,
        duplicate_detection_service=duplicate_detection_service,
        coverage_analysis_service=coverage_analysis_service,
        test_strategy_service=test_strategy_service,
        test_case_generation_service=test_case_generation_service,
        linking_service=linking_service,
    )

    return Container(
        settings=resolved,
        auth_provider=auth_provider,
        ado_client=ado_client,
        user_story_repository=user_story_repository,
        test_case_repository=test_case_repository,
        bug_repository=bug_repository,
        story_service=story_service,
        bug_service=bug_service,
        test_case_service=test_case_service,
        linking_service=linking_service,
        requirement_analysis_service=requirement_analysis_service,
        duplicate_detection_service=duplicate_detection_service,
        coverage_analysis_service=coverage_analysis_service,
        test_strategy_service=test_strategy_service,
        test_case_generation_service=test_case_generation_service,
        orchestration_service=orchestration_service,
    )
