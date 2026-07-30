"""Unit tests for Azure Repos Code Intelligence source resolution."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from qa_intelligence.domain.models.code_intelligence import CodeSourceKind
from qa_intelligence.domain.models.user_story import AcceptanceCriteria, UserStory
from qa_intelligence.infrastructure.config import Settings
from qa_intelligence.infrastructure.errors import ConfigurationError, UpstreamError
from qa_intelligence.services.ado_git_repository_service import AdoGitRepositoryService
from qa_intelligence.services.code_intelligence_service import CodeIntelligenceService


def _story() -> UserStory:
    return UserStory(
        id=7,
        title="Rename Fluid",
        description="Rename materials",
        acceptance_criteria=[AcceptanceCriteria(order=1, text="User can rename", id="AC-1")],
    )


def _settings(**overrides: Any) -> Settings:
    base = {
        "ado_organization": "Contoso",
        "ado_project": "FracPro",
        "ado_pat": "fake-pat-token",
        "ado_default_git_branch": "main",
    }
    base.update(overrides)
    return Settings(**base)


def test_ado_git_redacts_pat_in_errors() -> None:
    redacted = AdoGitRepositoryService._redact(
        "fatal: https://:fake-pat-token@dev.azure.com/x failed",
        "fake-pat-token",
    )
    assert "fake-pat-token" not in redacted
    assert "***" in redacted


def test_ado_git_clone_uses_depth_and_branch(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(list(cmd))
        if cmd[:2] == ["git", "--version"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="git version 2.0", stderr="")
        if cmd[:2] == ["git", "clone"]:
            target = Path(cmd[-1])
            (target / ".git").mkdir(parents=True)
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:2] == ["git", "rev-parse"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="abc123def456\n", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    settings = _settings(code_intel_cache_dir=str(tmp_path / "cache"))
    svc = AdoGitRepositoryService(settings, run_subprocess=fake_run)
    path, sha = svc.ensure_local_checkout("LivePlus", branch="develop")

    assert path.exists()
    assert sha == "abc123def456"
    clone = next(c for c in calls if c[:2] == ["git", "clone"])
    assert "--depth" in clone
    assert "1" in clone
    assert "--branch" in clone
    assert "develop" in clone
    # Authenticated URL must not be asserted in plaintext expectations beyond presence of @
    assert any("@" in part for part in clone)


def test_ado_git_clone_failure_is_upstream(tmp_path: Path) -> None:
    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if cmd[:2] == ["git", "--version"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="git version 2.0", stderr="")
        return subprocess.CompletedProcess(
            cmd,
            1,
            stdout="",
            stderr="fatal: Authentication failed for 'https://:fake-pat-token@dev.azure.com/x'",
        )

    settings = _settings(code_intel_cache_dir=str(tmp_path / "cache"))
    svc = AdoGitRepositoryService(settings, run_subprocess=fake_run)
    with pytest.raises(UpstreamError) as exc:
        svc.ensure_local_checkout("LivePlus")
    assert "fake-pat-token" not in str(exc.value)
    assert "fake-pat-token" not in str(exc.value.details)


def test_code_intel_prefers_ado_over_local(tmp_path: Path) -> None:
    local = tmp_path / "local"
    local.mkdir()
    (local / "ignored.txt").write_text("x", encoding="utf-8")

    ado_root = tmp_path / "ado_checkout"
    ado_root.mkdir()
    (ado_root / "RenameFluid.cs").write_text(
        "public class RenameFluid { /* rename fluid validation */ }\n",
        encoding="utf-8",
    )

    class FakeAdoGit:
        def ensure_local_checkout(self, repository: str, **kwargs: Any) -> tuple[Path, str | None]:
            assert repository == "LivePlus"
            assert kwargs.get("branch") == "main"
            return ado_root, "deadbeefcafebabe"

    summary = CodeIntelligenceService(
        ado_git_repository_service=FakeAdoGit(),  # type: ignore[arg-type]
    ).analyze(
        _story(),
        str(local),
        ado_repository="LivePlus",
        ado_branch="main",
        ado_project="FracPro",
    )

    assert summary.source_kind == CodeSourceKind.ADO_GIT
    assert summary.ado_repository == "LivePlus"
    assert summary.ado_branch == "main"
    assert summary.ado_commit == "deadbeefcafebabe"
    assert str(ado_root) in summary.repository_path
    assert "ignored" in summary.notes.lower() or "ado_repository" in summary.notes


def test_code_intel_requires_source() -> None:
    with pytest.raises(ConfigurationError):
        CodeIntelligenceService().analyze(_story())


def test_code_intel_uses_settings_default_repo(tmp_path: Path) -> None:
    ado_root = tmp_path / "default_repo"
    ado_root.mkdir()
    (ado_root / "Feature.cs").write_text("class RenameFluid {}\n", encoding="utf-8")

    class FakeAdoGit:
        def ensure_local_checkout(self, repository: str, **kwargs: Any) -> tuple[Path, str | None]:
            assert repository == "DefaultRepo"
            return ado_root, "111"

    summary = CodeIntelligenceService(
        ado_git_repository_service=FakeAdoGit(),  # type: ignore[arg-type]
        default_ado_repository="DefaultRepo",
        default_ado_branch="main",
    ).analyze(_story())

    assert summary.source_kind == CodeSourceKind.ADO_GIT
    assert summary.ado_repository == "DefaultRepo"
