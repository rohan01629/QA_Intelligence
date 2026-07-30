"""Code Intelligence domain models — implementation-aware analysis output."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import Field

from qa_intelligence.domain.models.base import DomainModel

NonEmptyStr = Annotated[str, Field(min_length=1)]


class CodeSourceKind(StrEnum):
    """Where Code Intelligence obtained the source tree."""

    LOCAL = "local"
    ADO_GIT = "ado_git"


class CodeArtifactRole(StrEnum):
    """Inferred role of a source file relative to the feature."""

    CONTROLLER = "controller"
    SERVICE = "service"
    REPOSITORY = "repository"
    COMMAND = "command"
    QUERY = "query"
    HANDLER = "handler"
    VALIDATOR = "validator"
    COMPONENT = "component"
    PAGE = "page"
    API_CLIENT = "api_client"
    DTO = "dto"
    MODEL = "model"
    CONFIG = "config"
    FEATURE_FLAG = "feature_flag"
    TEST = "test"
    OTHER = "other"


class AffectedFile(DomainModel):
    """A relevant source file discovered for the feature."""

    path: NonEmptyStr
    role: CodeArtifactRole = CodeArtifactRole.OTHER
    score: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    reason: str = ""


class AffectedApi(DomainModel):
    """An API endpoint or route inferred from source."""

    method: str = ""
    path: NonEmptyStr
    source_file: str | None = None
    notes: str = ""


class CodeSignal(DomainModel):
    """A concrete implementation signal used to drive test design."""

    kind: NonEmptyStr
    description: NonEmptyStr
    source_file: str | None = None
    evidence: str = ""


class ImplementationSummary(DomainModel):
    """Structured understanding of how a feature is implemented in code.

    Consumed by strategy / generation when present; never required for legacy paths.
    """

    feature: NonEmptyStr
    repository_path: NonEmptyStr
    source_kind: CodeSourceKind = CodeSourceKind.LOCAL
    ado_repository: str | None = None
    ado_project: str | None = None
    ado_branch: str | None = None
    ado_commit: str | None = None
    user_story_id: Annotated[int, Field(gt=0)] | None = None
    affected_files: list[AffectedFile] = Field(default_factory=list)
    affected_apis: list[AffectedApi] = Field(default_factory=list)
    business_rules: list[str] = Field(default_factory=list)
    validation_rules: list[str] = Field(default_factory=list)
    regression_areas: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    feature_flags: list[str] = Field(default_factory=list)
    integrations: list[str] = Field(default_factory=list)
    error_handling: list[str] = Field(default_factory=list)
    database_interactions: list[str] = Field(default_factory=list)
    ui_components: list[str] = Field(default_factory=list)
    signals: list[CodeSignal] = Field(default_factory=list)
    search_terms: list[str] = Field(default_factory=list)
    files_considered: Annotated[int, Field(ge=0)] = 0
    files_read: Annotated[int, Field(ge=0)] = 0
    notes: str = ""
