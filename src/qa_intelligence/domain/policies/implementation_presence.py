"""Rule 12 — prefer implemented US features; related-code generation is optional.

If the US feature is not implemented:
  1. Analyze previous/related implementation in configured codebases.
  2. Do not generate by default — ask the user first.
  3. Generate from related/legacy code only when the user approves
     (``allow_related_implementation=true``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from qa_intelligence.domain.models.code_intelligence import ImplementationSummary
from qa_intelligence.domain.models.user_story import UserStory

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")
_QUOTED_RE = re.compile(r'"([^"\n]{3,80})"')
_RENAME_RE = re.compile(
    r'(?i)rename\s+(?:the\s+)?"([^"]+)"\s+(?:button\s+)?to\s+"([^"]+)"'
)

_NOISE = frozenset(
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
        "fracpro",
        "live",
        "liveplus",
        "agile",
        "ops",
        "feature",
        "screen",
        "page",
        "button",
        "click",
        "clicking",
        "open",
        "opening",
        "show",
        "display",
        "update",
        "updated",
        "change",
        "rename",
        "verify",
        "ensure",
        "shall",
        "contain",
        "contains",
        "using",
        "based",
        "data",
        "value",
        "values",
        "field",
        "fields",
        "test",
        "case",
        "cases",
        "analysis",
        "reports",
        "report",
        "minifrac",
        "invoke",
        "launch",
        "action",
        "actions",
        "without",
        "saving",
        "changes",
        "modal",
        "dialog",
        "tabs",
        "tab",
        "plot",
        "plots",
        "displayed",
        "rendered",
        "scenario",
        "given",
        "moved",
        "move",
        "single",
        "existing",
        "instead",
        "creating",
        "occur",
        "immediately",
        "requiring",
        "refreshed",
        "refresh",
        "intersection",
        "position",
        "vertical",
        "curve",
    }
)

# Structural AC markers that must appear in implementation when the AC states them.
_STRUCTURAL_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("dialog", (r"\bdialog\b", r"\bmodal\b", r"mat-dialog", r"nz-modal", r"ngb-modal")),
    ("realtime_tab", (r"real[\s_-]*time", r"realtime", r"asciirealtime")),
    ("frpro_tab", (r"\bfrpro\b", r"fracpro\s*tab", r"asciifp", r"ascii[\s_-]*fp")),
    ("generate_action", (r"\bgenerate\b",)),
    ("cancel_action", (r"\bcancel\b",)),
)


@dataclass(frozen=True)
class ImplementationPresence:
    """Whether the US feature itself is implemented in scanned code."""

    found: bool
    reasons: tuple[str, ...] = ()
    paths_scanned: tuple[str, ...] = ()
    best_score: float = 0.0
    distinctive_hits: int = 0
    required_markers: tuple[str, ...] = ()
    matched_markers: tuple[str, ...] = ()
    missing_markers: tuple[str, ...] = ()


def _story_text(user_story: UserStory) -> str:
    parts = [
        user_story.title or "",
        user_story.description or "",
        *[ac.text for ac in user_story.acceptance_criteria if ac.text],
        *list(user_story.tags or []),
    ]
    return "\n".join(parts)


def required_implementation_markers(user_story: UserStory) -> list[str]:
    """Markers that must be present in source for the US feature to count as found."""
    text = _story_text(user_story)
    markers: list[str] = []
    seen: set[str] = set()
    skip_quotes: set[str] = set()

    def _add(label: str) -> None:
        key = label.strip().lower()
        if len(key) < 3 or key in seen:
            return
        seen.add(key)
        markers.append(label.strip())

    rename = _RENAME_RE.search(text)
    if rename:
        old_label = rename.group(1).strip(" \"'.")
        new_label = rename.group(2).strip(" \"'.")
        if old_label:
            skip_quotes.add(old_label.lower())
        if new_label:
            _add(f"rename_to:{new_label}")
            skip_quotes.add(new_label.lower())  # covered via rename_to

    # Quoted UI strings are strong requirements, except rename "from" labels.
    for match in _QUOTED_RE.findall(text):
        if match.lower() in skip_quotes:
            continue
        _add(f"quote:{match}")

    low = text.lower()
    for name, _patterns in _STRUCTURAL_MARKERS:
        trigger = {
            "dialog": ("dialog", "modal"),
            "realtime_tab": ("real-time", "realtime", "real time"),
            "frpro_tab": ("frpro",),
            "generate_action": ("generate",),
            "cancel_action": ("cancel",),
        }[name]
        if any(t in low for t in trigger):
            _add(f"struct:{name}")

    # Scenario-style ACs often have no quotes — require distinctive feature terms.
    if not markers:
        for tok in distinctive_feature_tokens(user_story)[:6]:
            _add(f"term:{tok}")

    return markers


def _content_blob(
    summary: ImplementationSummary,
    file_contents: dict[str, str] | None = None,
) -> str:
    parts: list[str] = []
    for af in summary.affected_files:
        parts.append(af.path.lower())
        parts.append((af.reason or "").lower())
        if file_contents:
            # Keys may be absolute or relative.
            for key, text in file_contents.items():
                if key.replace("\\", "/").endswith(af.path.replace("\\", "/")) or key == af.path:
                    parts.append(text.lower())
                    break
            else:
                # Also try joining repository_path + relative path.
                candidate = str(Path(summary.repository_path) / af.path)
                if candidate in file_contents:
                    parts.append(file_contents[candidate].lower())
    for signal in summary.signals:
        parts.append((signal.description or "").lower())
        parts.append((signal.evidence or "").lower())
    for item in (
        *summary.ui_components,
        *summary.validation_rules,
        *summary.business_rules,
        *[api.path for api in summary.affected_apis],
    ):
        parts.append(str(item).lower())
    return "\n".join(parts)


def _marker_present(marker: str, blob: str) -> bool:
    if marker.startswith("quote:"):
        needle = marker[len("quote:") :].lower()
        return needle in blob
    if marker.startswith("term:"):
        needle = marker[len("term:") :].lower()
        compact = needle.replace("-", "").replace("_", "")
        return needle in blob or compact in blob.replace("-", "").replace("_", "")
    if marker.startswith("rename_to:"):
        needle = marker[len("rename_to:") :].strip().lower()
        if not needle:
            return False
        compact = re.sub(r"[^a-z0-9]+", "_", needle).strip("_")
        exact_ui = (
            f'"{needle}"' in blob
            or f"'{needle}'" in blob
            or f">{needle}>" in blob
            or f">{needle} |" in blob
        )
        # Bare key/token (ASCII_REPORT) — not DOWNLOAD_ASCII_REPORT / GENERATE_ASCII_REPORT.
        bare_key = bool(
            re.search(
                rf"(?<![a-z0-9_]){re.escape(compact)}(?![a-z0-9_])",
                blob,
                flags=re.I,
            )
        )
        # If the only hits are inside download_/generate_ prefixes, reject.
        if bare_key:
            # Verify at least one match is not download_/generate_ prefixed.
            for match in re.finditer(
                rf"(?<![a-z0-9_]){re.escape(compact)}(?![a-z0-9_])",
                blob,
                flags=re.I,
            ):
                start = match.start()
                prefix = blob[max(0, start - 10) : start]
                if not prefix.endswith("download_") and not prefix.endswith("generate_"):
                    return True
            bare_key = False
        return exact_ui or bare_key
    if marker.startswith("struct:"):
        name = marker[len("struct:") :]
        patterns = dict(_STRUCTURAL_MARKERS).get(name, ())
        return any(re.search(p, blob, flags=re.I) for p in patterns)
    return marker.lower() in blob


def assess_summary_presence(
    summary: ImplementationSummary | None,
    user_story: UserStory,
    *,
    file_contents: dict[str, str] | None = None,
) -> ImplementationPresence:
    """US feature is found only when required AC markers exist in source content."""
    if summary is None:
        return ImplementationPresence(
            found=False,
            reasons=("no_implementation_summary",),
        )

    required = required_implementation_markers(user_story)
    blob = _content_blob(summary, file_contents)
    best_score = max((float(af.score or 0.0) for af in summary.affected_files), default=0.0)

    if not required:
        # No concrete AC markers → cannot prove the feature; do not generate.
        return ImplementationPresence(
            found=False,
            reasons=("no_required_markers_from_ac",),
            paths_scanned=(summary.repository_path,),
            best_score=best_score,
            required_markers=(),
        )

    matched = [m for m in required if _marker_present(m, blob)]
    missing = [m for m in required if m not in matched]

    # Require ALL structural/quote markers from AC — partial related code is not enough.
    found = len(missing) == 0 and best_score > 0

    reasons: list[str] = []
    if found:
        reasons.append(f"implemented_markers={len(matched)}/{len(required)}")
    else:
        reasons.append(f"missing_markers={','.join(missing[:12]) or 'all'}")
        if matched:
            reasons.append(f"partial_markers={','.join(matched[:12])}")

    return ImplementationPresence(
        found=found,
        reasons=tuple(reasons),
        paths_scanned=(summary.repository_path,),
        best_score=best_score,
        distinctive_hits=len(matched),
        required_markers=tuple(required),
        matched_markers=tuple(matched),
        missing_markers=tuple(missing),
    )


@dataclass(frozen=True)
class RelatedImplementation:
    """Previous/related code surface when the US feature itself is missing."""

    available: bool
    notes: str = ""
    file_paths: tuple[str, ...] = ()
    best_score: float = 0.0
    partial_markers: tuple[str, ...] = ()


def assess_related_implementation(
    summary: ImplementationSummary | None,
    user_story: UserStory,
    *,
    file_contents: dict[str, str] | None = None,
    presence: ImplementationPresence | None = None,
) -> RelatedImplementation:
    """Detect previous/related implementation usable for optional TC generation."""
    if summary is None:
        return RelatedImplementation(available=False, notes="no_implementation_summary")

    presence = presence or assess_summary_presence(
        summary,
        user_story,
        file_contents=file_contents,
    )
    if presence.found:
        return RelatedImplementation(
            available=False,
            notes="feature_already_found",
            best_score=presence.best_score,
        )

    # Strong related hits: high file score and/or partial AC markers.
    top_files = sorted(
        summary.affected_files,
        key=lambda f: float(f.score or 0.0),
        reverse=True,
    )[:8]
    related_paths = tuple(
        f.path for f in top_files if float(f.score or 0.0) >= 0.45
    )
    partial = presence.matched_markers
    available = bool(related_paths) or (
        presence.best_score >= 0.45 and bool(partial)
    ) or (summary.files_read > 0 and presence.best_score >= 0.7)

    if not available:
        return RelatedImplementation(
            available=False,
            notes="no_related_implementation_surface",
            best_score=presence.best_score,
            partial_markers=partial,
        )

    bits = [
        f"related_files={len(related_paths) or min(len(top_files), 5)}",
        f"best_score={presence.best_score:.3f}",
    ]
    if partial:
        bits.append(f"partial_markers={','.join(partial[:8])}")
    if presence.missing_markers:
        bits.append(f"still_missing={','.join(presence.missing_markers[:8])}")
    paths = related_paths or tuple(f.path for f in top_files[:5])
    return RelatedImplementation(
        available=True,
        notes="; ".join(bits),
        file_paths=paths,
        best_score=presence.best_score,
        partial_markers=partial,
    )


def assess_related_across_summaries(
    summaries: list[ImplementationSummary],
    user_story: UserStory,
    *,
    file_contents_by_repo: dict[str, dict[str, str]] | None = None,
) -> RelatedImplementation:
    """Related surface exists if any scanned tree has related/legacy evidence."""
    best: RelatedImplementation | None = None
    notes: list[str] = []
    paths: list[str] = []
    any_available = False
    for summary in summaries:
        contents = None
        if file_contents_by_repo:
            contents = file_contents_by_repo.get(summary.repository_path)
        related = assess_related_implementation(
            summary,
            user_story,
            file_contents=contents,
        )
        notes.append(f"{summary.repository_path} => {related.notes}")
        if related.available:
            any_available = True
            paths.extend(related.file_paths)
        if best is None or related.best_score > best.best_score or (
            related.available and not best.available
        ):
            best = related
    return RelatedImplementation(
        available=any_available,
        notes="; ".join(notes),
        file_paths=tuple(dict.fromkeys(paths)),
        best_score=(best.best_score if best else 0.0),
        partial_markers=(best.partial_markers if best else ()),
    )


def confirmation_prompt_for_related(
    *,
    user_story: UserStory,
    related: RelatedImplementation,
    presence_notes: str = "",
) -> str:
    """User-facing prompt when feature is missing but related code exists."""
    files = ", ".join(related.file_paths[:6]) or "(see Code Intelligence files)"
    return (
        f"Rule 12: User Story #{user_story.id} feature is not implemented yet "
        f"('{user_story.title}'). "
        f"Related/previous implementation was found in the codebase "
        f"(files: {files}). "
        "TC generation is optional. "
        "Do you want to generate test cases based on this related/existing "
        "implementation? "
        "Reply yes to proceed with related-based drafts, or no to skip. "
        f"Details: {related.notes}. {presence_notes}"
    ).strip()


def assess_presence_across_summaries(
    summaries: list[ImplementationSummary],
    user_story: UserStory,
    *,
    file_contents_by_repo: dict[str, dict[str, str]] | None = None,
) -> ImplementationPresence:
    """Feature is found if **any** scanned codebase implements the US markers."""
    if not summaries:
        return ImplementationPresence(
            found=False,
            reasons=("no_codebases_scanned",),
        )

    best: ImplementationPresence | None = None
    all_paths: list[str] = []
    any_found = False
    reasons: list[str] = []
    for summary in summaries:
        contents = None
        if file_contents_by_repo:
            contents = file_contents_by_repo.get(summary.repository_path)
        presence = assess_summary_presence(
            summary,
            user_story,
            file_contents=contents,
        )
        all_paths.extend(presence.paths_scanned)
        reasons.append(
            f"{summary.repository_path} => "
            f"{'found' if presence.found else 'missing'} ({'; '.join(presence.reasons)})"
        )
        if presence.found:
            any_found = True
        if best is None or presence.best_score > best.best_score or (
            presence.found and not best.found
        ):
            best = presence

    return ImplementationPresence(
        found=any_found,
        reasons=tuple(reasons),
        paths_scanned=tuple(dict.fromkeys(all_paths)),
        best_score=(best.best_score if best else 0.0),
        distinctive_hits=(best.distinctive_hits if best else 0),
        required_markers=(best.required_markers if best else ()),
        matched_markers=(best.matched_markers if best else ()),
        missing_markers=(best.missing_markers if best else ()),
    )


# Kept for older tests / callers that only need tokens.
def distinctive_feature_tokens(user_story: UserStory) -> list[str]:
    """Extract story-specific tokens (debug / search assist)."""
    corpus = _story_text(user_story).lower().replace("-", " ").replace("_", " ")
    counts: dict[str, int] = {}
    for raw in _TOKEN_RE.findall(corpus):
        tok = raw.lower().strip("-_")
        if len(tok) < 4 or tok in _NOISE:
            continue
        counts[tok] = counts.get(tok, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
    return [tok for tok, _ in ranked[:30]]
