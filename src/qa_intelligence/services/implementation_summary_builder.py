"""ImplementationSummaryBuilder — assemble ImplementationSummary from analysis parts."""

from __future__ import annotations

from qa_intelligence.domain.models.code_intelligence import (
    AffectedFile,
    CodeSourceKind,
    ImplementationSummary,
)
from qa_intelligence.domain.models.user_story import UserStory


class ImplementationSummaryBuilder:
    """Build the structured ImplementationSummary object."""

    def build(
        self,
        *,
        user_story: UserStory,
        repository_path: str,
        search_terms: list[str],
        affected_files: list[AffectedFile],
        files_considered: int,
        files_read: int,
        impact: dict[str, object],
        notes: str = "",
        source_kind: CodeSourceKind = CodeSourceKind.LOCAL,
        ado_repository: str | None = None,
        ado_project: str | None = None,
        ado_branch: str | None = None,
        ado_commit: str | None = None,
    ) -> ImplementationSummary:
        feature = user_story.title.strip() or "Unknown feature"
        default_notes = (
            f"Analyzed {files_read} of {len(affected_files)} selected files "
            f"for feature '{feature}'"
        )
        if source_kind == CodeSourceKind.ADO_GIT:
            default_notes += (
                f" from Azure Repos '{ado_repository}' "
                f"branch '{ado_branch or 'unknown'}'"
            )
            if ado_commit:
                default_notes += f" @ {ado_commit[:12]}"
        default_notes += "."
        return ImplementationSummary(
            feature=feature,
            repository_path=repository_path,
            source_kind=source_kind,
            ado_repository=ado_repository,
            ado_project=ado_project,
            ado_branch=ado_branch,
            ado_commit=ado_commit,
            user_story_id=user_story.id,
            affected_files=affected_files,
            affected_apis=list(impact.get("affected_apis") or []),  # type: ignore[arg-type]
            business_rules=list(impact.get("business_rules") or []),  # type: ignore[arg-type]
            validation_rules=list(impact.get("validation_rules") or []),  # type: ignore[arg-type]
            regression_areas=list(impact.get("regression_areas") or []),  # type: ignore[arg-type]
            permissions=list(impact.get("permissions") or []),  # type: ignore[arg-type]
            feature_flags=list(impact.get("feature_flags") or []),  # type: ignore[arg-type]
            integrations=list(impact.get("integrations") or []),  # type: ignore[arg-type]
            error_handling=list(impact.get("error_handling") or []),  # type: ignore[arg-type]
            database_interactions=list(impact.get("database_interactions") or []),  # type: ignore[arg-type]
            ui_components=list(impact.get("ui_components") or []),  # type: ignore[arg-type]
            signals=list(impact.get("signals") or []),  # type: ignore[arg-type]
            search_terms=search_terms,
            files_considered=files_considered,
            files_read=files_read,
            notes=notes or default_notes,
        )
