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
from qa_intelligence.domain.policies.implementation_presence import (
    assess_presence_across_summaries,
    assess_related_across_summaries,
    assess_related_implementation,
    assess_summary_presence,
    confirmation_prompt_for_related,
)
from qa_intelligence.domain.policies.local_repository_paths import (
    local_paths_for_code_intelligence,
    parse_local_repository_paths,
    select_local_repository_path,
)
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
        default_local_repository_paths: list[str] | None = None,
    ) -> None:
        self._search = repository_search_service or RepositorySearchService()
        self._impact = impact_analysis_service or ImpactAnalysisService()
        self._builder = implementation_summary_builder or ImplementationSummaryBuilder()
        self._ado_git = ado_git_repository_service
        self._default_ado_repository = (default_ado_repository or "").strip() or None
        self._default_ado_branch = (default_ado_branch or "").strip() or None
        self._default_ado_project = (default_ado_project or "").strip() or None
        self._default_local_repository_paths = list(default_local_repository_paths or [])

    @property
    def has_default_ado_repository(self) -> bool:
        """True when settings provide a default Azure Repos name."""
        return self._default_ado_repository is not None

    @property
    def has_default_local_repository(self) -> bool:
        """True when at least one configured local app path exists on disk."""
        return (
            select_local_repository_path(
                self._default_local_repository_paths,
                require_existing=True,
            )
            is not None
        )

    def configured_local_repository_paths(
        self,
        *,
        require_existing: bool = True,
        user_story: UserStory | None = None,
    ) -> list[str]:
        """Return local roots for scanning (QA-state Live+ stories use QA tree, not UAT)."""
        return local_paths_for_code_intelligence(
            self._default_local_repository_paths,
            user_story=user_story,
            require_existing=require_existing,
        )

    def resolve_local_repository_path(
        self,
        repository_path: str | None = None,
        *,
        user_story: UserStory | None = None,
    ) -> str | None:
        """Explicit path wins; otherwise pick best configured local root for the story."""
        explicit = (repository_path or "").strip() or None
        if explicit:
            return explicit
        return select_local_repository_path(
            self._default_local_repository_paths,
            user_story=user_story,
            require_existing=True,
        )

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
        scan_all_local: bool | None = None,
    ) -> ImplementationSummary:
        """Search relevant files, analyze impact, and return ImplementationSummary.

        When multiple local roots are configured and no Azure Repos source is used,
        Rule 12 scans **all** existing local roots. Generation is allowed only if
        feature evidence is found in at least one tree.
        """
        repo_name = (ado_repository or self._default_ado_repository or "").strip() or None
        local_roots = self.configured_local_repository_paths(
            require_existing=True,
            user_story=user_story,
        )
        should_scan_all = (
            scan_all_local
            if scan_all_local is not None
            else (repo_name is None and len(local_roots) > 1 and not (repository_path or "").strip())
        )

        if should_scan_all and local_roots:
            return self._analyze_all_local(
                user_story,
                local_roots,
                related_bugs=related_bugs,
                extra_terms=extra_terms,
                max_files=max_files,
            )

        effective_local = self.resolve_local_repository_path(
            repository_path,
            user_story=user_story,
        )
        resolved = self._resolve_source(
            repository_path=effective_local,
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

        summary = self._analyze_root(
            user_story,
            root,
            related_bugs=related_bugs,
            extra_terms=extra_terms,
            max_files=max_files,
            source_kind=resolved["source_kind"],  # type: ignore[arg-type]
            ado_repository=resolved.get("ado_repository"),  # type: ignore[arg-type]
            ado_project=resolved.get("ado_project"),  # type: ignore[arg-type]
            ado_branch=resolved.get("ado_branch"),  # type: ignore[arg-type]
            ado_commit=resolved.get("ado_commit"),  # type: ignore[arg-type]
            notes=str(resolved.get("notes") or ""),
        )
        # Re-read contents for Rule 12 marker checks.
        contents = self._search.read_files(root, summary.affected_files)
        presence = assess_summary_presence(
            summary,
            user_story,
            file_contents=contents,
        )
        summary.feature_found = presence.found
        summary.feature_presence_notes = "; ".join(presence.reasons)
        if presence.missing_markers:
            summary.feature_presence_notes += (
                f"; missing={','.join(presence.missing_markers[:12])}"
            )
        summary.scanned_repository_paths = list(presence.paths_scanned)
        if not presence.found:
            related = assess_related_implementation(
                summary,
                user_story,
                file_contents=contents,
                presence=presence,
            )
            summary.related_implementation_available = related.available
            summary.related_implementation_notes = related.notes
            summary.related_file_paths = list(related.file_paths)
        logger.info(
            "code_intel.completed",
            user_story_id=user_story.id,
            feature=summary.feature,
            source_kind=summary.source_kind.value,
            files_read=summary.files_read,
            feature_found=summary.feature_found,
            related_available=summary.related_implementation_available,
            ado_repository=summary.ado_repository,
            ado_branch=summary.ado_branch,
        )
        return summary

    def _analyze_all_local(
        self,
        user_story: UserStory,
        local_roots: list[str],
        *,
        related_bugs: list[Bug] | None,
        extra_terms: list[str] | None,
        max_files: int | None,
    ) -> ImplementationSummary:
        summaries: list[ImplementationSummary] = []
        contents_by_repo: dict[str, dict[str, str]] = {}
        for root in local_roots:
            try:
                summary = self._analyze_root(
                    user_story,
                    Path(root),
                    related_bugs=related_bugs,
                    extra_terms=extra_terms,
                    max_files=max_files,
                    source_kind=CodeSourceKind.LOCAL,
                    notes=f"Source: local path '{root}'.",
                )
                contents = self._search.read_files(Path(root), summary.affected_files)
                summaries.append(summary)
                contents_by_repo[summary.repository_path] = contents
            except (OSError, NotFoundError) as exc:
                logger.warning(
                    "code_intel.local_scan_failed",
                    repository_path=root,
                    error=str(exc),
                )

        presence = assess_presence_across_summaries(
            summaries,
            user_story,
            file_contents_by_repo=contents_by_repo,
        )
        if not summaries:
            raise ConfigurationError(
                "No local repository paths could be scanned for Code Intelligence",
                details={"configured": local_roots},
            )

        ranked = sorted(
            summaries,
            key=lambda s: (
                1
                if assess_summary_presence(
                    s,
                    user_story,
                    file_contents=contents_by_repo.get(s.repository_path),
                ).found
                else 0,
                max((f.score for f in s.affected_files), default=0.0),
                s.files_read,
            ),
            reverse=True,
        )
        best = ranked[0]
        best.feature_found = presence.found
        best.feature_presence_notes = "; ".join(presence.reasons)
        if presence.missing_markers:
            best.feature_presence_notes += (
                f"; missing={','.join(presence.missing_markers[:12])}"
            )
        best.scanned_repository_paths = list(presence.paths_scanned)
        if not presence.found:
            related = assess_related_across_summaries(
                summaries,
                user_story,
                file_contents_by_repo=contents_by_repo,
            )
            best.related_implementation_available = related.available
            best.related_implementation_notes = related.notes
            best.related_file_paths = list(related.file_paths)
        note = (
            f"Scanned {len(summaries)} local codebase(s). "
            f"Rule 12 feature_found={presence.found}."
        )
        best.notes = f"{best.notes} {note}".strip()
        logger.info(
            "code_intel.multi_local_completed",
            user_story_id=user_story.id,
            scanned=len(summaries),
            feature_found=presence.found,
            related_available=best.related_implementation_available,
            chosen_path=best.repository_path,
        )
        return best

    def _analyze_root(
        self,
        user_story: UserStory,
        root: Path,
        *,
        related_bugs: list[Bug] | None,
        extra_terms: list[str] | None,
        max_files: int | None,
        source_kind: CodeSourceKind,
        ado_repository: str | None = None,
        ado_project: str | None = None,
        ado_branch: str | None = None,
        ado_commit: str | None = None,
        notes: str = "",
    ) -> ImplementationSummary:
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
        return self._builder.build(
            user_story=user_story,
            repository_path=str(root),
            search_terms=search_terms,
            affected_files=affected_files,
            files_considered=len(affected_files),
            files_read=len(contents),
            impact=impact,
            source_kind=source_kind,
            ado_repository=ado_repository,
            ado_project=ado_project,
            ado_branch=ado_branch,
            ado_commit=ado_commit,
            notes=notes,
        )

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
            "(or set CODE_INTEL_LOCAL_REPOSITORY_PATHS / ADO_DEFAULT_GIT_REPOSITORY in .env)"
        )
