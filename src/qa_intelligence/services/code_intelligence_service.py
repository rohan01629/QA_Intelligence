"""CodeIntelligenceService — facade for codebase-aware feature analysis.

Does not replace requirement analysis, coverage, or generation.
Produces an ImplementationSummary for optional downstream enrichment.

Source resolution:
  1. ``ado_repository`` (tool arg or settings default) → shallow Azure Repos checkout
  2. else ``repository_path`` → local filesystem
  3. else ConfigurationError

When both ADO and local are provided, Azure Repos wins (latest shared branch).
Use local-only for uncommitted WIP.
"""

from __future__ import annotations

from pathlib import Path

import structlog

from qa_intelligence.domain.models.bug import Bug
from qa_intelligence.domain.models.code_intelligence import CodeSourceKind, ImplementationSummary
from qa_intelligence.domain.models.user_story import UserStory
from qa_intelligence.infrastructure.errors import ConfigurationError, NotFoundError
from qa_intelligence.services.ado_git_repository_service import AdoGitRepositoryService
from qa_intelligence.services.impact_analysis_service import ImpactAnalysisService
from qa_intelligence.services.implementation_summary_builder import ImplementationSummaryBuilder
from qa_intelligence.services.repository_search_service import RepositorySearchService

logger = structlog.get_logger(__name__)


class CodeIntelligenceService:
    """Understand likely implementation impact for a User Story against source."""

    def __init__(
        self,
        *,
        repository_search_service: RepositorySearchService | None = None,
        impact_analysis_service: ImpactAnalysisService | None = None,
        implementation_summary_builder: ImplementationSummaryBuilder | None = None,
        ado_git_repository_service: AdoGitRepositoryService | None = None,
        default_ado_repository: str | None = None,
        default_ado_branch: str | None = None,
        default_ado_project: str | None = None,
    ) -> None:
        self._search = repository_search_service or RepositorySearchService()
        self._impact = impact_analysis_service or ImpactAnalysisService()
        self._builder = implementation_summary_builder or ImplementationSummaryBuilder()
        self._ado_git = ado_git_repository_service
        self._default_ado_repository = (default_ado_repository or "").strip() or None
        self._default_ado_branch = (default_ado_branch or "").strip() or None
        self._default_ado_project = (default_ado_project or "").strip() or None

    @property
    def has_default_ado_repository(self) -> bool:
        """True when settings provide a default Azure Repos name."""
        return self._default_ado_repository is not None

    def analyze(
        self,
        user_story: UserStory,
        repository_path: str | None = None,
        *,
        ado_repository: str | None = None,
        ado_branch: str | None = None,
        ado_project: str | None = None,
        related_bugs: list[Bug] | None = None,
        extra_terms: list[str] | None = None,
        max_files: int | None = None,
        refresh_ado: bool = True,
    ) -> ImplementationSummary:
        """Search relevant files, analyze impact, and return ImplementationSummary."""
        resolved = self._resolve_source(
            repository_path=repository_path,
            ado_repository=ado_repository,
            ado_branch=ado_branch,
            ado_project=ado_project,
            refresh_ado=refresh_ado,
        )
        root = Path(str(resolved["path"]))
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
            source_kind=resolved["source_kind"],  # type: ignore[arg-type]
            ado_repository=resolved.get("ado_repository"),  # type: ignore[arg-type]
            ado_project=resolved.get("ado_project"),  # type: ignore[arg-type]
            ado_branch=resolved.get("ado_branch"),  # type: ignore[arg-type]
            ado_commit=resolved.get("ado_commit"),  # type: ignore[arg-type]
            notes=str(resolved.get("notes") or ""),
        )
        logger.info(
            "code_intel.completed",
            user_story_id=user_story.id,
            feature=summary.feature,
            source_kind=summary.source_kind.value,
            files_read=summary.files_read,
            apis=len(summary.affected_apis),
            rules=len(summary.validation_rules),
            ado_repository=summary.ado_repository,
            ado_branch=summary.ado_branch,
            ado_commit=summary.ado_commit,
        )
        return summary

    def _resolve_source(
        self,
        *,
        repository_path: str | None,
        ado_repository: str | None,
        ado_branch: str | None,
        ado_project: str | None,
        refresh_ado: bool,
    ) -> dict[str, object]:
        repo_name = (ado_repository or self._default_ado_repository or "").strip() or None
        branch = (ado_branch or self._default_ado_branch or "").strip() or None
        project = (ado_project or self._default_ado_project or "").strip() or None
        local = (repository_path or "").strip() or None

        if repo_name:
            if self._ado_git is None:
                raise ConfigurationError(
                    "ado_repository was requested but Azure Repos git service is not configured"
                )
            if local:
                logger.info(
                    "code_intel.prefer_ado_over_local",
                    ado_repository=repo_name,
                    ignored_local_path=local,
                )
            path, sha = self._ado_git.ensure_local_checkout(
                repo_name,
                branch=branch,
                project=project,
                refresh=refresh_ado,
            )
            notes = (
                f"Source: Azure Repos '{repo_name}' "
                f"(branch '{branch or 'default'}'"
                + (f", commit {sha[:12]}" if sha else "")
                + ")."
            )
            if local:
                notes += f" Local path '{local}' was ignored because ado_repository was set."
            return {
                "path": str(path),
                "source_kind": CodeSourceKind.ADO_GIT,
                "ado_repository": repo_name,
                "ado_project": project,
                "ado_branch": branch,
                "ado_commit": sha,
                "notes": notes,
            }

        if local:
            root = Path(local).expanduser().resolve()
            return {
                "path": str(root),
                "source_kind": CodeSourceKind.LOCAL,
                "ado_repository": None,
                "ado_project": None,
                "ado_branch": None,
                "ado_commit": None,
                "notes": f"Source: local path '{root}'.",
            }

        raise ConfigurationError(
            "Provide repository_path and/or ado_repository "
            "(or set ADO_DEFAULT_GIT_REPOSITORY in .env)"
        )
