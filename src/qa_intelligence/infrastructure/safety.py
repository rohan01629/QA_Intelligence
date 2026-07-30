"""Safety guards — prevent accidental Azure DevOps / Azure Repos mutations."""

from __future__ import annotations

from qa_intelligence.infrastructure.config import Settings
from qa_intelligence.infrastructure.errors import ConfigurationError

# Git subcommands that touch only the local cache (or read from remote).
_ALLOWED_GIT_HEADS: frozenset[str] = frozenset(
    {
        "--version",
        "clone",
        "fetch",
        "checkout",
        "rev-parse",
        "remote",
        "config",
    }
)

# Never run these against Azure Repos from this product.
_FORBIDDEN_GIT_TOKENS: frozenset[str] = frozenset(
    {
        "push",
        "commit",
        "merge",
        "rebase",
        "cherry-pick",
        "tag",
        "stash",
        "reset",
        "clean",
        "branch",
        "pull",  # use fetch + local checkout only
        "am",
        "revert",
        "filter-branch",
        "gc",
        "reflog",
    }
)

PUSH_DISABLED_URL = "DISABLED_READ_ONLY_NO_PUSH"


def assert_git_command_read_only(cmd: list[str]) -> None:
    """Raise if a git argv looks like it could mutate a remote or rewrite history."""
    if not cmd:
        raise ConfigurationError("Empty git command blocked by safety guard")

    # cmd[0] is git executable; first subcommand token after options
    tokens = [t for t in cmd[1:] if t and not t.startswith("-")]
    if not tokens:
        # pure flags like git --version
        if any(t == "--version" for t in cmd[1:]):
            return
        raise ConfigurationError("Unrecognized git command blocked by safety guard")

    head = tokens[0]
    if head not in _ALLOWED_GIT_HEADS:
        raise ConfigurationError(
            f"Blocked git subcommand '{head}' — Code Intelligence is read-only "
            "against Azure Repos (no push/commit/branch changes on remote)",
            details={"command_head": head},
        )

    lowered = {t.lower() for t in cmd[1:] if not t.startswith("-")}
    for bad in _FORBIDDEN_GIT_TOKENS:
        if bad in lowered:
            raise ConfigurationError(
                f"Blocked forbidden git token '{bad}' — Azure Repos access is read-only",
                details={"token": bad},
            )

    # Extra: never allow `git remote add` with push mirrors etc. — set-url + get-url only
    if head == "remote" and len(tokens) >= 2:
        remote_action = tokens[1]
        if remote_action not in {"set-url", "get-url", "-v", "show"}:
            raise ConfigurationError(
                f"Blocked git remote action '{remote_action}' — only set-url/get-url allowed",
                details={"remote_action": remote_action},
            )


def ensure_ado_writes_allowed(settings: Settings, *, dry_run: bool, action: str) -> None:
    """Block real ADO work-item writes unless explicitly enabled and not dry-run."""
    if dry_run:
        return
    if settings.ado_writes_enabled:
        return
    raise ConfigurationError(
        f"Refusing to {action} in Azure DevOps: ADO_WRITES_ENABLED is false. "
        "Drafts may be validated with dry_run=true. To create/link for real, set "
        "ADO_WRITES_ENABLED=true in .env and call with dry_run=false only after approval.",
        details={"action": action, "ado_writes_enabled": False},
    )
