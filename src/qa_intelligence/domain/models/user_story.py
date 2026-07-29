"""User story and acceptance criteria models."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, field_validator

from qa_intelligence.domain.models.base import DomainModel

NonEmptyStr = Annotated[str, Field(min_length=1)]


class AcceptanceCriteria(DomainModel):
    """A single acceptance criterion for a user story."""

    order: Annotated[int, Field(ge=1)] = Field(
        ...,
        description="1-based position among acceptance criteria",
    )
    text: NonEmptyStr = Field(..., description="Acceptance criterion statement")
    id: str | None = Field(
        default=None,
        description="Optional stable identifier (e.g. AC-1)",
    )

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Acceptance criteria text must not be blank")
        return value.strip()


class UserStory(DomainModel):
    """Azure DevOps user story as understood by QA Intelligence."""

    id: Annotated[int, Field(gt=0)]
    title: NonEmptyStr
    description: str = ""
    acceptance_criteria: list[AcceptanceCriteria] = Field(default_factory=list)
    state: NonEmptyStr = "New"
    area_path: str = ""
    iteration_path: str = ""
    tags: list[str] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("User story title must not be blank")
        return value.strip()

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, values: list[str]) -> list[str]:
        return [tag.strip() for tag in values if tag and tag.strip()]
