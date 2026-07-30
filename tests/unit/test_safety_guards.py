"""Unit tests for ADO / Azure Repos safety guards."""

from __future__ import annotations

import pytest

from qa_intelligence.infrastructure.config import Settings
from qa_intelligence.infrastructure.errors import ConfigurationError
from qa_intelligence.infrastructure.safety import (
    assert_git_command_read_only,
    ensure_ado_writes_allowed,
)


def test_git_allows_clone_and_fetch() -> None:
    assert_git_command_read_only(["git", "clone", "--depth", "1", "url", "dir"])
    assert_git_command_read_only(["git", "fetch", "--depth", "1", "origin", "main"])
    assert_git_command_read_only(
        ["git", "remote", "set-url", "--push", "origin", "DISABLED_READ_ONLY_NO_PUSH"]
    )


def test_git_blocks_push_and_commit() -> None:
    with pytest.raises(ConfigurationError, match="read-only"):
        assert_git_command_read_only(["git", "push", "origin", "main"])
    with pytest.raises(ConfigurationError, match="read-only"):
        assert_git_command_read_only(["git", "commit", "-m", "x"])
    with pytest.raises(ConfigurationError, match="Blocked"):
        assert_git_command_read_only(["git", "branch", "-D", "tmp"])


def test_ado_writes_blocked_by_default() -> None:
    settings = Settings(
        ado_organization="o",
        ado_project="p",
        ado_pat="t",
        ado_writes_enabled=False,
    )
    ensure_ado_writes_allowed(settings, dry_run=True, action="create_test_cases")
    with pytest.raises(ConfigurationError, match="ADO_WRITES_ENABLED"):
        ensure_ado_writes_allowed(settings, dry_run=False, action="create_test_cases")


def test_ado_writes_allowed_when_enabled() -> None:
    settings = Settings(
        ado_organization="o",
        ado_project="p",
        ado_pat="t",
        ado_writes_enabled=True,
    )
    ensure_ado_writes_allowed(settings, dry_run=False, action="link_test_cases")
