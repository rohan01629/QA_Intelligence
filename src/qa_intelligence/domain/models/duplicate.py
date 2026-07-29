"""Duplicate analysis domain models."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from qa_intelligence.domain.enums import DuplicateBasis
from qa_intelligence.domain.models.base import DomainModel
from qa_intelligence.domain.models.coverage import ScenarioRef

NonEmptyStr = Annotated[str, Field(min_length=1)]


class DuplicateCluster(DomainModel):
    """A set of scenarios that share the same business intent."""

    canonical: ScenarioRef
    duplicates: list[ScenarioRef] = Field(min_length=1)
    similarity: Annotated[float, Field(ge=0.0, le=1.0)]
    basis: DuplicateBasis
    explanation: str = ""


class DuplicateAnalysis(DomainModel):
    """Result of semantic duplicate detection across candidates and inventory."""

    user_story_id: Annotated[int, Field(gt=0)] | None = None
    clusters: list[DuplicateCluster] = Field(default_factory=list)
    duplicate_scenario_count: Annotated[int, Field(ge=0)] = 0
    threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.82
    notes: str = ""

    @classmethod
    def from_clusters(
        cls,
        *,
        clusters: list[DuplicateCluster],
        user_story_id: int | None = None,
        threshold: float = 0.82,
        notes: str = "",
    ) -> DuplicateAnalysis:
        """Build analysis and derive duplicate_scenario_count from clusters."""
        count = sum(len(cluster.duplicates) for cluster in clusters)
        return cls(
            user_story_id=user_story_id,
            clusters=clusters,
            duplicate_scenario_count=count,
            threshold=threshold,
            notes=notes,
        )
