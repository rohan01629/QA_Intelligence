"""Read models returned by repository adapters (not MCP write contracts)."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from qa_intelligence.domain.models.base import DomainModel

NonEmptyStr = Annotated[str, Field(min_length=1)]


class TestCaseSummary(DomainModel):
    """Inventory / search projection of an Azure DevOps Test Case."""

    __test__ = False

    id: Annotated[int, Field(gt=0)]
    title: NonEmptyStr
    steps: list[str] = Field(default_factory=list)
    expected_results: list[str] = Field(default_factory=list)
    state: NonEmptyStr = "Unknown"
    link_type: str | None = None
    area_path: str | None = None

    @property
    def steps_preview(self) -> list[str]:
        return self.steps

    @property
    def expected_preview(self) -> list[str]:
        return self.expected_results


class RelatedWorkItemRef(DomainModel):
    """Lightweight relation pointer from a work item."""

    id: Annotated[int, Field(gt=0)]
    link_type: NonEmptyStr
    url: str | None = None
