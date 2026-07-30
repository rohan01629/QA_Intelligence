"""RepositorySearchService — smart, limited retrieval of feature-relevant files."""

from __future__ import annotations

import re
from pathlib import Path

import structlog

from qa_intelligence.domain.models.bug import Bug
from qa_intelligence.domain.models.code_intelligence import AffectedFile, CodeArtifactRole
from qa_intelligence.domain.models.user_story import UserStory

logger = structlog.get_logger(__name__)

_SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "dist",
        "build",
        "out",
        "target",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "coverage",
        "htmlcov",
        ".idea",
        ".vscode",
        "bin",
        "obj",
    }
)

_SOURCE_SUFFIXES = frozenset(
    {
        ".cs",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".py",
        ".java",
        ".kt",
        ".go",
        ".rb",
        ".php",
        ".vue",
        ".svelte",
        ".json",
        ".yml",
        ".yaml",
        ".xml",
        ".sql",
    }
)

_ROLE_PATTERNS: tuple[tuple[CodeArtifactRole, re.Pattern[str]], ...] = (
    (CodeArtifactRole.CONTROLLER, re.compile(r"controller", re.I)),
    (CodeArtifactRole.HANDLER, re.compile(r"handler", re.I)),
    (CodeArtifactRole.COMMAND, re.compile(r"command", re.I)),
    (CodeArtifactRole.QUERY, re.compile(r"query", re.I)),
    (CodeArtifactRole.VALIDATOR, re.compile(r"validat", re.I)),
    (CodeArtifactRole.REPOSITORY, re.compile(r"repository|repo\b", re.I)),
    (CodeArtifactRole.SERVICE, re.compile(r"service", re.I)),
    (CodeArtifactRole.API_CLIENT, re.compile(r"api[_-]?client|httpclient|axios", re.I)),
    (CodeArtifactRole.DTO, re.compile(r"\bdto\b|request|response", re.I)),
    (CodeArtifactRole.MODEL, re.compile(r"model|entity", re.I)),
    (CodeArtifactRole.PAGE, re.compile(r"page|screen|view", re.I)),
    (CodeArtifactRole.COMPONENT, re.compile(r"component|dialog|modal|\.tsx$|\.jsx$", re.I)),
    (CodeArtifactRole.FEATURE_FLAG, re.compile(r"feature[_-]?flag|launchdarkly|unleash", re.I)),
    (CodeArtifactRole.CONFIG, re.compile(r"config|settings|appsettings", re.I)),
    (CodeArtifactRole.TEST, re.compile(r"test|spec", re.I)),
)

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9]{2,}")
_STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "when",
        "user",
        "story",
        "should",
        "must",
        "will",
        "able",
        "into",
        "than",
        "then",
        "also",
        "have",
        "been",
        "were",
        "are",
        "was",
        "can",
        "not",
    }
)


class RepositorySearchService:
    """Infer search terms and return a ranked shortlist of relevant source files."""

    def __init__(
        self,
        *,
        max_files_to_consider: int = 4000,
        max_files_to_return: int = 25,
    ) -> None:
        self._max_files_to_consider = max_files_to_consider
        self._max_files_to_return = max_files_to_return

    def infer_search_terms(
        self,
        user_story: UserStory,
        *,
        related_bugs: list[Bug] | None = None,
        extra_terms: list[str] | None = None,
    ) -> list[str]:
        parts: list[str] = [
            user_story.title,
            user_story.description,
            *[ac.text for ac in user_story.acceptance_criteria],
            *user_story.tags,
        ]
        for bug in related_bugs or []:
            parts.append(bug.title)
            if bug.repro_steps:
                parts.append(bug.repro_steps)
        for term in extra_terms or []:
            parts.append(term)

        corpus = " ".join(parts)
        tokens = [
            tok.lower()
            for tok in _TOKEN_RE.findall(corpus)
            if tok.lower() not in _STOPWORDS
        ]
        # Prefer longer / repeated tokens.
        counts: dict[str, int] = {}
        for tok in tokens:
            counts[tok] = counts.get(tok, 0) + 1
        ranked = sorted(counts.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
        terms = [tok for tok, _ in ranked[:24]]

        # Keep camel/pascal chunks from title as whole phrases.
        for phrase in re.findall(r"[A-Z][a-z]+(?:[A-Z][a-z]+)+", user_story.title):
            lowered = phrase.lower()
            if lowered not in terms:
                terms.insert(0, lowered)
        return terms

    def search(
        self,
        repository_path: str | Path,
        search_terms: list[str],
        *,
        max_files: int | None = None,
    ) -> list[AffectedFile]:
        root = Path(repository_path).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise FileNotFoundError(f"Repository path not found or not a directory: {root}")

        limit = max_files if max_files and max_files > 0 else self._max_files_to_return
        terms = [t.lower() for t in search_terms if t and t.strip()]
        if not terms:
            terms = ["feature"]

        candidates: list[AffectedFile] = []
        considered = 0
        for path in root.rglob("*"):
            if considered >= self._max_files_to_consider:
                break
            if not path.is_file():
                continue
            if any(part in _SKIP_DIR_NAMES for part in path.parts):
                continue
            if path.suffix.lower() not in _SOURCE_SUFFIXES:
                continue
            considered += 1

            rel = path.relative_to(root).as_posix()
            name = path.name.lower()
            rel_lower = rel.lower()
            score = 0.0
            matched: list[str] = []
            for term in terms:
                if term in name:
                    score += 0.45
                    matched.append(term)
                elif term in rel_lower:
                    score += 0.25
                    matched.append(term)
            if score <= 0:
                continue

            # Light content peek for stronger ranking (first 8KB only).
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")[:8192].lower()
            except OSError:
                text = ""
            for term in terms[:12]:
                if term in text:
                    score += 0.15
                    if term not in matched:
                        matched.append(term)

            score = min(score, 1.0)
            role = self._infer_role(rel, name)
            candidates.append(
                AffectedFile(
                    path=rel,
                    role=role,
                    score=round(score, 3),
                    reason=f"matched: {', '.join(matched[:6])}",
                )
            )

        candidates.sort(key=lambda item: (-item.score, item.path))
        selected = candidates[:limit]
        logger.info(
            "code_intel.search_completed",
            repository=str(root),
            considered=considered,
            matched=len(candidates),
            selected=len(selected),
        )
        return selected

    def read_files(
        self,
        repository_path: str | Path,
        files: list[AffectedFile],
    ) -> dict[str, str]:
        root = Path(repository_path).expanduser().resolve()
        contents: dict[str, str] = {}
        for item in files:
            full = root / item.path
            try:
                contents[item.path] = full.read_text(encoding="utf-8", errors="ignore")[:50_000]
            except OSError as exc:
                logger.warning("code_intel.read_failed", path=item.path, error=str(exc))
        return contents

    def _infer_role(self, rel_path: str, name: str) -> CodeArtifactRole:
        haystack = f"{rel_path} {name}"
        for role, pattern in _ROLE_PATTERNS:
            if pattern.search(haystack):
                return role
        return CodeArtifactRole.OTHER
