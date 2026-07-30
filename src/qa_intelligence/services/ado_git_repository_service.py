"""Shallow clone / refresh Azure Repos for Code Intelligence (read-only remote)."""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from urllib.parse import quote

import structlog

from qa_intelligence.infrastructure.config import Settings
from qa_intelligence.infrastructure.errors import ConfigurationError, UpstreamError
from qa_intelligence.infrastructure.safety import (
    PUSH_DISABLED_URL,
    assert_git_command_read_only,
)

logger = structlog.get_logger(__name__)

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")
RunSubprocess = Callable[..., subprocess.CompletedProcess[str]]


class AdoGitRepositoryService:
    """Ensure a local checkout of an Azure DevOps Git repository.

    **Remote is read-only:** only ``clone`` / ``fetch`` against Azure Repos.
    Never ``push``, ``commit``, or mutate remote branches. Local cache only.
    The PAT is never written to logs.
    """

    def __init__(
        self,
        settings: Settings,
        *,
        git_executable: str = "git",
        run_subprocess: RunSubprocess | None = None,
    ) -> None:
        self._settings = settings
        self._git = git_executable
        self._run: RunSubprocess = run_subprocess or subprocess.run

    def ensure_local_checkout(
        self,
        repository: str,
        *,
        branch: str | None = None,
        project: str | None = None,
        organization: str | None = None,
        refresh: bool = True,
    ) -> tuple[Path, str | None]:
        """Clone or refresh a shallow checkout; return ``(path, commit_sha)``."""
        repo = (repository or "").strip()
        if not repo:
            raise ConfigurationError("ado_repository is required for Azure Repos checkout")

        org = (organization or self._settings.ado_organization or "").strip()
        proj = (project or self._settings.ado_project or "").strip()
        br = (branch or self._settings.ado_default_git_branch or "main").strip()
        # Users often say origin/main-uat; clone/fetch need the remote branch name only.
        if br.startswith("origin/"):
            br = br[len("origin/") :].lstrip()
        if br.startswith("refs/heads/"):
            br = br[len("refs/heads/") :].lstrip()
        pat = (self._settings.ado_pat or "").strip()

        if not org or not proj:
            raise ConfigurationError(
                "ADO_ORGANIZATION and ADO_PROJECT are required to clone from Azure Repos",
                details={"organization": org or None, "project": proj or None},
            )
        if not pat:
            raise ConfigurationError(
                "ADO_PAT is required to clone from Azure Repos "
                "(needs Code Read scope only — do not grant Code Write)"
            )

        self._assert_git_available()

        cache_root = self._cache_root()
        target = cache_root / self._cache_dirname(org, proj, repo, br)
        auth_url = self._auth_clone_url(org, proj, repo, pat)
        public_url = self._public_clone_url(org, proj, repo)

        if target.exists() and (target / ".git").is_dir():
            if refresh:
                self._refresh(target, auth_url, br, public_url=public_url)
        else:
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            target.parent.mkdir(parents=True, exist_ok=True)
            self._clone(auth_url, target, br, public_url=public_url)

        self._disable_push(target, public_url=public_url)
        sha = self._rev_parse(target)
        logger.info(
            "ado_git.checkout_ready",
            repository=repo,
            project=proj,
            branch=br,
            path=str(target),
            commit=sha,
            public_url=public_url,
            remote_mode="read_only",
        )
        return target, sha

    def _assert_git_available(self) -> None:
        try:
            result = self._run(
                [self._git, "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ConfigurationError(
                "git executable not found on PATH; install Git to use ado_repository"
            ) from exc
        if result.returncode != 0:
            raise ConfigurationError(
                "git is not usable on this machine",
                details={"stderr": (result.stderr or "")[:200]},
            )

    def _cache_root(self) -> Path:
        configured = (self._settings.code_intel_cache_dir or "").strip()
        if configured:
            root = Path(configured).expanduser().resolve()
        else:
            root = Path.home() / ".cache" / "qa_intelligence" / "ado_git"
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _cache_dirname(org: str, project: str, repo: str, branch: str) -> str:
        raw = f"{org}|{project}|{repo}|{branch}".lower()
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
        label = _SAFE_NAME.sub("_", f"{repo}_{branch}")[:60].strip("._") or "repo"
        return f"{label}_{digest}"

    def _public_clone_url(self, org: str, project: str, repo: str) -> str:
        base = self._settings.ado_base_url.rstrip("/")
        return (
            f"{base}/{quote(org, safe='')}/"
            f"{quote(project, safe='')}/_git/{quote(repo, safe='')}"
        )

    def _auth_clone_url(self, org: str, project: str, repo: str, pat: str) -> str:
        base = self._settings.ado_base_url.rstrip("/")
        return (
            f"{base.replace('https://', 'https://:' + quote(pat, safe='') + '@', 1)}/"
            f"{quote(org, safe='')}/"
            f"{quote(project, safe='')}/_git/{quote(repo, safe='')}"
        )

    def _clone(self, auth_url: str, target: Path, branch: str, *, public_url: str) -> None:
        cmd = [
            self._git,
            "clone",
            "--depth",
            "1",
            "--branch",
            branch,
            "--single-branch",
            auth_url,
            str(target),
        ]
        self._exec(cmd, cwd=None, public_url=public_url, action="clone")

    def _refresh(
        self,
        target: Path,
        auth_url: str,
        branch: str,
        *,
        public_url: str,
    ) -> None:
        self._exec(
            [self._git, "remote", "set-url", "origin", auth_url],
            cwd=target,
            public_url=public_url,
            action="set-url",
        )
        self._exec(
            [self._git, "fetch", "--depth", "1", "origin", branch],
            cwd=target,
            public_url=public_url,
            action="fetch",
        )
        # Local tracking branch only — does not create/update remote branch.
        self._exec(
            [self._git, "checkout", "-B", branch, "FETCH_HEAD"],
            cwd=target,
            public_url=public_url,
            action="checkout",
        )
        self._exec(
            [self._git, "remote", "set-url", "origin", public_url],
            cwd=target,
            public_url=public_url,
            action="scrub-url",
        )

    def _disable_push(self, target: Path, *, public_url: str) -> None:
        """Make accidental ``git push`` fail even if someone runs it in the cache."""
        self._exec(
            [self._git, "remote", "set-url", "--push", "origin", PUSH_DISABLED_URL],
            cwd=target,
            public_url=public_url,
            action="disable-push",
        )

    def _rev_parse(self, target: Path) -> str | None:
        result = self._run(
            [self._git, "rev-parse", "HEAD"],
            cwd=str(target),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        return (result.stdout or "").strip() or None

    def _exec(
        self,
        cmd: list[str],
        *,
        cwd: Path | None,
        public_url: str,
        action: str,
    ) -> None:
        assert_git_command_read_only(cmd)
        result = self._run(
            cmd,
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return
        stderr = self._redact(result.stderr or "", self._settings.ado_pat)
        stdout = self._redact(result.stdout or "", self._settings.ado_pat)
        logger.error(
            "ado_git.command_failed",
            action=action,
            public_url=public_url,
            returncode=result.returncode,
            stderr=stderr[:500],
        )
        raise UpstreamError(
            f"Azure Repos git {action} failed for {public_url}",
            details={
                "action": action,
                "returncode": result.returncode,
                "stderr": stderr[:500],
                "stdout": stdout[:200],
            },
        )

    @staticmethod
    def _redact(text: str, pat: str) -> str:
        redacted = text
        if pat:
            redacted = redacted.replace(pat, "***")
            redacted = redacted.replace(quote(pat, safe=""), "***")
        redacted = re.sub(r"https://:[^@]+@", "https://:***@", redacted)
        redacted = re.sub(r"https://[^:@/]+:[^@]+@", "https://:***@", redacted)
        return redacted
