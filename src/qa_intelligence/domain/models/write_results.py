"""Write-path result models (create / link)."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from qa_intelligence.domain.enums import CreateStatus, LinkStatus
from qa_intelligence.domain.models.base import DomainModel


class CreateResult(DomainModel):
    """Per-item outcome of validate / create."""

    __test__ = False

    index: Annotated[int, Field(ge=0)]
    status: CreateStatus
    id: Annotated[int, Field(gt=0)] | None = None
    title: str | None = None
    validation_errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    message: str | None = None


class LinkResult(DomainModel):
    """Per-item outcome of linking a test case to a user story."""

    __test__ = False

    test_case_id: Annotated[int, Field(gt=0)]
    status: LinkStatus
    message: str | None = None
