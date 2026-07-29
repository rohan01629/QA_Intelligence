"""Shared text helpers for deterministic requirement signal matching."""

from __future__ import annotations

import re

from qa_intelligence.domain.models.user_story import UserStory


def story_corpus(story: UserStory) -> str:
    """Build a lowercase searchable corpus from story fields."""
    parts = [
        story.title,
        story.description,
        story.area_path,
        " ".join(story.tags),
        " ".join(ac.text for ac in story.acceptance_criteria),
    ]
    return " ".join(parts).lower()


def contains_phrase(text: str, phrase: str) -> bool:
    """Match multi-word phrases as substrings; single tokens with word boundaries."""
    phrase = phrase.strip().lower()
    if not phrase:
        return False
    if " " in phrase:
        return phrase in text
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None


def contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(contains_phrase(text, phrase) for phrase in phrases)


def contains_any_positive(text: str, phrases: tuple[str, ...]) -> bool:
    """Like contains_any, but ignore matches that appear in a negation context."""
    for phrase in phrases:
        if not contains_phrase(text, phrase):
            continue
        if _is_negated(text, phrase):
            continue
        return True
    return False


def _is_negated(text: str, phrase: str) -> bool:
    """Return True when the phrase is preceded by no/not/without/excluding."""
    phrase = phrase.strip().lower()
    if " " in phrase:
        pattern = rf"\b(?:no|not|without|excluding)\s+{re.escape(phrase)}\b"
    else:
        pattern = rf"\b(?:no|not|without|excluding)\s+{re.escape(phrase)}\b"
    return re.search(pattern, text) is not None


def find_matches(text: str, phrases: tuple[str, ...]) -> list[str]:
    return [phrase for phrase in phrases if contains_phrase(text, phrase)]


def extract_rule_like_lines(story: UserStory) -> list[str]:
    """Extract candidate business/validation rules from AC and description."""
    rules: list[str] = []
    for ac in story.acceptance_criteria:
        text = ac.text.strip()
        if text:
            rules.append(text)

    rule_pattern = re.compile(
        r"\b(must|should|shall|if|when|validate|reject|ensure|only|cannot|can't)\b",
        re.IGNORECASE,
    )
    for line in re.split(r"[\r\n]+", story.description or ""):
        cleaned = re.sub(r"<[^>]+>", " ", line).strip(" \t-•*")
        if len(cleaned) < 8:
            continue
        if rule_pattern.search(cleaned):
            rules.append(cleaned)

    seen: set[str] = set()
    unique: list[str] = []
    for rule in rules:
        key = rule.lower()
        if key not in seen:
            seen.add(key)
            unique.append(rule)
    return unique


def extract_module_candidates(story: UserStory) -> list[str]:
    """Infer modules from area path segments and tagged tokens."""
    modules: list[str] = []
    if story.area_path:
        segments = [
            s.strip()
            for s in story.area_path.replace("/", "\\").split("\\")
            if s.strip()
        ]
        if len(segments) > 1:
            modules.extend(segments[1:])
        elif segments:
            modules.append(segments[0])
    for tag in story.tags:
        if tag and tag.lower() not in {m.lower() for m in modules}:
            modules.append(tag)
    return modules


def extract_dependency_candidates(corpus: str, story: UserStory) -> list[str]:
    """Heuristic dependency mentions from corpus."""
    dependency_patterns = (
        r"depends on ([a-z0-9 _.-]{3,40})",
        r"integrat(?:e|es|ion) with ([a-z0-9 _.-]{3,40})",
        r"calls? ([a-z0-9 _.-]{3,40}) (?:api|service)",
        r"downstream ([a-z0-9 _.-]{3,40})",
        r"third[- ]party ([a-z0-9 _.-]{3,40})",
    )
    found: list[str] = []
    for pattern in dependency_patterns:
        for match in re.finditer(pattern, corpus, flags=re.IGNORECASE):
            name = match.group(1).strip(" .,;:")
            if name and name not in found:
                found.append(name)
    for tag in story.tags:
        lowered = tag.lower()
        if any(token in lowered for token in ("api", "service", "client", "gateway")):
            if tag not in found:
                found.append(tag)
    return found
