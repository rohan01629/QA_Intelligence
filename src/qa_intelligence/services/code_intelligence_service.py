"""CodeIntelligenceService — facade for codebase-aware feature analysis.

Does not replace requirement analysis, coverage, or generation.
Produces an ImplementationSummary for optional downstream enrichment.
"""

from __future__ import annotations

from pathlib import Path

import structlog

from qa_intelligence.domain.models.bug import Bug
from qa_intelligence.domain.models.code_intelligence import ImplementationSummary
from qa_intelligence.domain.models.user_story import UserStory
from qa_intelligence.infrastructure.errors import ConfigurationError, NotFoundError
from qa_intelligence.services.impact_analysis_service import ImpactAnalysisService
from qa_intelligence.services.implementation_summary_builder import ImplementationSummaryBuilder
from qa_intelligence.services.repository_search_service import RepositorySearchService

logger = structlog.get_logger(__name__)


class CodeIntelligenceService:
    """Understand likely implementation impact for a User Story against a local repo."""

    def __init__(
        self,
        *,
        repository_search_service: RepositorySearchService | None = None,
        impact_analysis_service: ImpactAnalysisService | None = None,
        implementation_summary_builder: ImplementationSummaryBuilder | None = None,
    ) -> None:
        self._search = repository_search_service or RepositorySearchService()
        self._impact = impact_analysis_service or ImpactAnalysisService()
        self._builder = implementation_summary_builder or ImplementationSummaryBuilder()

    def analyze(
        self,
        user_story: UserStory,
        repository_path: str,
        *,
        related_bugs: list[Bug] | None = None,
        extra_terms: list[str] | None = None,
        max_files: int | None = None,
    ) -> ImplementationSummary:
        """Search relevant files, analyze impact, and return ImplementationSummary."""
        if not repository_path or not repository_path.strip():
            raise ConfigurationError("repository_path is required for code intelligence")

        root = Path(repository_path).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise NotFoundError(
                f"Repository path not found: {root}",
                details={"repository_path": str(root)},
            )

        search_terms = self._search.infer_search_terms(
            user_story,
            related_bugs=related_bugs,
            extra_terms=extra_terms,
        )
        affected_files = self._search.search(root, search_terms, max_files=max_files)
        contents = self._search.read_files(root, affected_files)
        impact = self._impact.analyze(
            affected_files,
            contents,
            feature_name=user_story.title,
        )
        summary = self._builder.build(
            user_story=user_story,
            repository_path=str(root),
            search_terms=search_terms,
            affected_files=affected_files,
            files_considered=len(affected_files),
            files_read=len(contents),
            impact=impact,
        )
        logger.info(
            "code_intel.completed",
            user_story_id=user_story.id,
            feature=summary.feature,
            files_read=summary.files_read,
            apis=len(summary.affected_apis),
            rules=len(summary.validation_rules),
        )
        return summary
