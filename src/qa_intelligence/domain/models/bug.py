"""Bug domain model."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, field_validator

from qa_intelligence.domain.models.base import DomainModel

NonEmptyStr = Annotated[str, Field(min_length=1)]


class Bug(DomainModel):
    """Related defect used for regression / bug-covered scenario analysis."""

    id: Annotated[int, Field(gt=0)]
    title: NonEmptyStr
    state: NonEmptyStr
    severity: str | None = None
    repro_steps: str | None = None
    area_path: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Bug title must not be blank")
        return value.strip()

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, values: list[str]) -> list[str]:
        return [tag.strip() for tag in values if tag and tag.strip()]
