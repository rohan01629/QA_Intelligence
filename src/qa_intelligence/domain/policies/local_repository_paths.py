"""Resolve which local application codebase to analyze for a User Story."""

from __future__ import annotations

import re
from pathlib import Path

from qa_intelligence.domain.models.user_story import UserStory

# Live+ UAT folder names → QA (e.g. ...\Live_Plus_UAT → ...\Live_Plus_QA).
_LIVE_PLUS_UAT_PATTERN = re.compile(r"live[_-]?plus[_-]?uat", re.IGNORECASE)

# Keyword boosts for story → path matching (path string + story text).
_PATH_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "minifrac",
        (
            "minifrac",
            "mini-frac",
            "loglog",
            "log-log",
            "log log",
            "g-func",
            "gfunc",
            "g-function",
            "isip",
            "sqrt plot",
            "closure stress",
            "magenta circle",
            "auto pick",
            "tangent",
        ),
    ),
        (
            "live_plus",
            (
                "live+",
                "live +",
                "live_plus",
                "live-plus",
                "plot",
                "plots",
                "template",
                "save plot",
                "save template",
                "channel",
                "ascii report",
                "download ascii",
                "material selection",
                "proppant",
                "witsml",
                "word report",
                "report-buttons",
                "report buttons",
            ),
        ),
)


def parse_local_repository_paths(raw: str | list[str] | None) -> list[str]:
    """Split env / settings into distinct local repository roots."""
    if raw is None:
        return []
    if isinstance(raw, list):
        parts = raw
    else:
        text = str(raw).replace("\r\n", "\n").replace(";", "\n").replace(",", "\n")
        parts = text.split("\n")
    out: list[str] = []
    seen: set[str] = set()
    for part in parts:
        cleaned = part.strip().strip('"').strip("'")
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
    return out


def _story_preferred_bucket(user_story: UserStory | None, extra_text: str | None = None) -> str | None:
    """Which codebase family the story text most strongly signals."""
    blob = _story_blob(user_story, extra_text)
    best_bucket: str | None = None
    best_hits = 0
    for hint_bucket, keywords in _PATH_HINTS:
        hits = sum(1 for kw in keywords if kw in blob)
        if hits > best_hits:
            best_hits = hits
            best_bucket = hint_bucket
    return best_bucket if best_hits > 0 else None


def _story_blob(user_story: UserStory | None, extra_text: str | None = None) -> str:
    if user_story is None:
        return (extra_text or "").lower()
    bits = [user_story.title or ""]
    bits.extend(ac.text for ac in user_story.acceptance_criteria if ac.text)
    if extra_text:
        bits.append(extra_text)
    return "\n".join(bits).lower()


def _path_bucket(path: str) -> str | None:
    low = path.replace("\\", "/").lower()
    if "minifrac" in low:
        return "minifrac"
    if "live_plus_qa" in low or "live-plus-qa" in low or "liveplusqa" in low:
        return "live_plus_qa"
    if "live_plus" in low or "live-plus" in low or "liveplus" in low:
        return "live_plus"
    return None


def score_local_repository_path(
    path: str,
    *,
    user_story: UserStory | None = None,
    extra_text: str | None = None,
) -> int:
    """Higher score = better match for this story against this local tree."""
    blob = _story_blob(user_story, extra_text)
    score = 0
    root = Path(path)
    if root.exists() and root.is_dir():
        score += 5
    bucket = _path_bucket(path)
    for hint_bucket, keywords in _PATH_HINTS:
        hits = sum(1 for kw in keywords if kw in blob)
        if hits == 0:
            continue
        if bucket == hint_bucket:
            score += 20 + hits * 3
        elif hint_bucket == "live_plus" and bucket == "live_plus_qa":
            score += 15 + hits * 3
        else:
            score += hits
    if _is_qa_state(user_story) and bucket == "live_plus_qa":
        if _story_preferred_bucket(user_story, extra_text) in (None, "live_plus"):
            score += 25
    # Prefer fracpro-agile leaf when both parent and child are listed.
    if path.replace("\\", "/").lower().rstrip("/").endswith("fracpro-agile"):
        score += 2
    return score


def _is_qa_state(user_story: UserStory | None) -> bool:
    return user_story is not None and (user_story.state or "").strip().lower() == "qa"


def derive_live_plus_qa_path(path: str) -> str | None:
    """Map a Live+ UAT local path to its QA counterpart (same suffix structure)."""
    match = _LIVE_PLUS_UAT_PATTERN.search(path)
    if not match:
        return None
    token = match.group(0)
    if "UAT" in token:
        replacement = token.replace("UAT", "QA")
    elif "uat" in token:
        replacement = token.replace("uat", "qa")
    else:
        replacement = re.sub(r"uat", "qa", token, flags=re.IGNORECASE)
    return f"{path[:match.start()]}{replacement}{path[match.end():]}"


def _prefer_fracpro_agile_leaf(path: str) -> str:
    """When a repo root contains fracpro-agile, use that leaf for Code Intelligence."""
    root = Path(path).expanduser()
    child = root / "fracpro-agile"
    if child.is_dir():
        return str(child.resolve())
    if root.is_dir():
        return str(root.resolve())
    return path


def expand_local_repository_paths(
    paths: list[str],
    *,
    user_story: UserStory | None = None,
) -> list[str]:
    """Return configured paths, plus derived QA Live+ roots when the story is in QA state."""
    candidates = parse_local_repository_paths(paths)
    if not _is_qa_state(user_story):
        return candidates

    out: list[str] = list(candidates)
    seen = {p.lower() for p in out}
    for path in candidates:
        if _path_bucket(path) != "live_plus":
            continue
        derived = derive_live_plus_qa_path(path)
        if not derived:
            continue
        derived = _prefer_fracpro_agile_leaf(derived)
        key = derived.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(derived)
    return out


def local_paths_for_code_intelligence(
    paths: list[str],
    *,
    user_story: UserStory | None = None,
    require_existing: bool = True,
) -> list[str]:
    """Paths to scan for Code Intelligence (QA-state Live+ uses QA tree, not UAT)."""
    expanded = expand_local_repository_paths(paths, user_story=user_story)
    filtered: list[str] = []
    seen: set[str] = set()
    for path in expanded:
        if _is_qa_state(user_story) and _path_bucket(path) == "live_plus":
            continue
        root = Path(path).expanduser()
        if require_existing and (not root.exists() or not root.is_dir()):
            continue
        resolved = _prefer_fracpro_agile_leaf(path)
        key = resolved.lower()
        if key in seen:
            continue
        seen.add(key)
        filtered.append(resolved)
    return filtered


def _find_live_plus_qa_path(
    candidates: list[str],
    *,
    require_existing: bool,
) -> str | None:
    for path in candidates:
        if _path_bucket(path) != "live_plus_qa":
            continue
        root = Path(path).expanduser()
        if require_existing and (not root.exists() or not root.is_dir()):
            continue
        return _prefer_fracpro_agile_leaf(path)
    return None


def select_local_repository_path(
    paths: list[str],
    *,
    user_story: UserStory | None = None,
    extra_text: str | None = None,
    require_existing: bool = True,
) -> str | None:
    """Pick the best configured local path for Code Intelligence.

    Returns ``None`` when no candidates remain.
    """
    candidates = expand_local_repository_paths(paths, user_story=user_story)
    if not candidates:
        return None
    if _is_qa_state(user_story):
        candidates = [p for p in candidates if _path_bucket(p) != "live_plus"]

    ranked: list[tuple[int, str]] = []
    for path in candidates:
        root = Path(path).expanduser()
        if require_existing and (not root.exists() or not root.is_dir()):
            continue
        ranked.append(
            (
                score_local_repository_path(
                    path,
                    user_story=user_story,
                    extra_text=extra_text,
                ),
                path,
            )
        )
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], item[1].lower()))
    chosen = ranked[0][1]
    if _is_qa_state(user_story) and _path_bucket(chosen) == "live_plus":
        qa_path = _find_live_plus_qa_path(candidates, require_existing=require_existing)
        return qa_path
    return _prefer_fracpro_agile_leaf(chosen)
