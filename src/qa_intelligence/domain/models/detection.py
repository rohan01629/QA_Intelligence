"""Duplicate detection result models."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from qa_intelligence.domain.enums import DuplicateBasis, ScenarioDisposition
from qa_intelligence.domain.models.base import DomainModel
from qa_intelligence.domain.models.duplicate import DuplicateCluster

NonEmptyStr = Annotated[str, Field(min_length=1)]


class ScenarioMatch(DomainModel):
    """A scenario classified against the user story and existing inventory."""

    key: NonEmptyStr
    title: NonEmptyStr
    disposition: ScenarioDisposition
    similarity: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    basis: DuplicateBasis | None = None
    matched_test_case_ids: list[Annotated[int, Field(gt=0)]] = Field(default_factory=list)
    matched_bug_ids: list[Annotated[int, Field(gt=0)]] = Field(default_factory=list)
    related_ac_ids: list[str] = Field(default_factory=list)
    explanation: str = ""
    is_similar: bool = False
    is_obsolete: bool = False
    is_bug_covered: bool = False


class DuplicateDetectionResult(DomainModel):
    """Structured output of DuplicateDetectionService."""

    user_story_id: Annotated[int, Field(gt=0)]
    duplicate: list[ScenarioMatch] = Field(default_factory=list)
    covered: list[ScenarioMatch] = Field(default_factory=list)
    needs_update: list[ScenarioMatch] = Field(default_factory=list)
    generate_new: list[ScenarioMatch] = Field(default_factory=list)
    similar: list[ScenarioMatch] = Field(
        default_factory=list,
        description="Similar but non-duplicate pairs / near-matches",
    )
    obsolete: list[ScenarioMatch] = Field(
        default_factory=list,
        description="Existing tests with weak relevance to current AC",
    )
    bug_covered: list[ScenarioMatch] = Field(
        default_factory=list,
        description="Scenarios already evidenced by related bugs",
    )
    clusters: list[DuplicateCluster] = Field(default_factory=list)
    duplicate_threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.82
    similar_threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.65
    covered_threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.72
