"""Requirement gap detection policy — report incompleteness; do not invent AC."""

from __future__ import annotations

from qa_intelligence.domain.enums import (
    FeatureType,
    GapSeverity,
    RequirementGapType,
)
from qa_intelligence.domain.models.analysis import RequirementGap
from qa_intelligence.domain.models.user_story import UserStory
from qa_intelligence.domain.policies.signals import contains_any, story_corpus


def detect_requirement_gaps(
    story: UserStory,
    feature_type: FeatureType,
) -> list[RequirementGap]:
    gaps: list[RequirementGap] = []
    corpus = story_corpus(story)
    description = (story.description or "").strip()
    ac_count = len(story.acceptance_criteria)

    if ac_count == 0:
        gaps.append(
            RequirementGap(
                type=RequirementGapType.AMBIGUOUS_AC,
                severity=GapSeverity.BLOCKING,
                description="Acceptance criteria are missing.",
                evidence="acceptance_criteria is empty",
            )
        )
        gaps.append(
            RequirementGap(
                type=RequirementGapType.MISSING_EXPECTED_BEHAVIOR,
                severity=GapSeverity.BLOCKING,
                description="Expected behavior cannot be verified without acceptance criteria.",
                evidence="No AC entries available to map expected outcomes",
            )
        )

    if ac_count > 0:
        vague = [
            ac
            for ac in story.acceptance_criteria
            if _is_vague(ac.text)
        ]
        if vague:
            gaps.append(
                RequirementGap(
                    type=RequirementGapType.AMBIGUOUS_AC,
                    severity=GapSeverity.WARNING,
                    description="One or more acceptance criteria are ambiguous.",
                    evidence="; ".join(ac.text for ac in vague[:3]),
                )
            )

    if len(description) < 20 and ac_count == 0:
        gaps.append(
            RequirementGap(
                type=RequirementGapType.MISSING_EXPECTED_BEHAVIOR,
                severity=GapSeverity.BLOCKING,
                description="Description is too thin to infer expected behavior.",
                evidence=f"description_length={len(description)}",
            )
        )

    api_like = feature_type in {
        FeatureType.BACKEND_API,
        FeatureType.API,
        FeatureType.INTEGRATION,
    }
    error_signals = (
        "error",
        "fail",
        "invalid",
        "exception",
        "4xx",
        "5xx",
        "timeout",
        "reject",
    )
    validation_signals = (
        "validate",
        "validation",
        "required field",
        "mandatory",
        "schema",
        "constraint",
    )

    if api_like and ac_count > 0 and not contains_any(corpus, error_signals):
        gaps.append(
            RequirementGap(
                type=RequirementGapType.MISSING_ERROR_HANDLING,
                severity=GapSeverity.WARNING,
                description="Error handling behavior is not specified.",
                evidence="No error/failure/status language found in story corpus",
            )
        )

    if api_like and ac_count > 0 and not contains_any(corpus, validation_signals):
        gaps.append(
            RequirementGap(
                type=RequirementGapType.MISSING_VALIDATION,
                severity=GapSeverity.WARNING,
                description="Input validation rules are not explicitly stated.",
                evidence="No validation language found in story corpus",
            )
        )

    if _has_conflict_markers(corpus):
        gaps.append(
            RequirementGap(
                type=RequirementGapType.CONFLICTING_REQUIREMENTS,
                severity=GapSeverity.WARNING,
                description="Potential conflicting requirements detected.",
                evidence="Found opposing must/must not style markers in corpus",
            )
        )

    return _dedupe_gaps(gaps)


def _is_vague(text: str) -> bool:
    lowered = text.lower().strip()
    vague_phrases = (
        "as expected",
        "works correctly",
        "works fine",
        "should work",
        "etc.",
        "and so on",
        "handle appropriately",
    )
    if len(lowered) < 12:
        return True
    return any(phrase in lowered for phrase in vague_phrases)


def _has_conflict_markers(corpus: str) -> bool:
    return ("must not" in corpus and " must " in corpus) or (
        "cannot" in corpus and "must" in corpus and "cannot" in corpus
    )


def _dedupe_gaps(gaps: list[RequirementGap]) -> list[RequirementGap]:
    seen: set[tuple[str, str]] = set()
    unique: list[RequirementGap] = []
    for gap in gaps:
        key = (gap.type.value, gap.description)
        if key in seen:
            continue
        seen.add(key)
        unique.append(gap)
    return unique
