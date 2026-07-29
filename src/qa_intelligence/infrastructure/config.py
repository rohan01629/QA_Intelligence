"""Application settings loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for Azure DevOps and HTTP client."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    ado_organization: str = Field(default="", description="Azure DevOps organization name")
    ado_project: str = Field(default="", description="Azure DevOps project name")
    ado_base_url: str = "https://dev.azure.com"
    ado_api_version: str = "7.1"
    ado_pat: str = Field(default="", description="Azure DevOps Personal Access Token")

    ado_default_test_plan_id: int | None = None
    ado_default_suite_id: int | None = None

    ado_user_story_type: str = "User Story"
    ado_test_case_type: str = "Test Case"
    ado_bug_type: str = "Bug"
    ado_ac_field: str | None = "Microsoft.VSTS.Common.AcceptanceCriteria"
    ado_tested_by_relation: str = "Microsoft.VSTS.Common.TestedBy-Forward"

    mcp_transport: str = "stdio"
    log_level: str = "INFO"

    http_timeout_seconds: float = 30.0
    http_max_retries: int = Field(default=3, ge=0)

    duplicate_threshold: float = Field(default=0.82, ge=0.0, le=1.0)
    create_reject_duplicates: bool = True

    @field_validator(
        "ado_default_test_plan_id",
        "ado_default_suite_id",
        "ado_ac_field",
        mode="before",
    )
    @classmethod
    def empty_str_to_none(cls, value: object) -> object:
        if value == "" or value is None:
            return None
        return value

    @field_validator("ado_base_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @property
    def ado_project_base(self) -> str:
        """Base URL for project-scoped REST APIs."""
        org = self.ado_organization.strip("/")
        project = self.ado_project
        return f"{self.ado_base_url}/{org}/{project}"

    @property
    def ado_org_base(self) -> str:
        """Base URL for organization-scoped REST APIs."""
        org = self.ado_organization.strip("/")
        return f"{self.ado_base_url}/{org}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings loader for the process."""
    return Settings()  # type: ignore[call-arg]


def clear_settings_cache() -> None:
    """Clear cached settings (tests)."""
    get_settings.cache_clear()
