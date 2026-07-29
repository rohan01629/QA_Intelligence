"""Duplicate guard — enforce Rule 1 (never generate / publish duplicates)."""

from __future__ import annotations

from qa_intelligence.domain.models.read_models import TestCaseSummary
from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.domain.policies.product_rules import DUPLICATE_SIMILARITY_THRESHOLD
from qa_intelligence.domain.similarity import (
    FeatureSimilarityScorer,
    ScenarioText,
    SimilarityScorer,
)


def is_duplicate_of_existing(
    draft: TestCase,
    existing: list[TestCaseSummary] | list[TestCase],
    *,
    scorer: SimilarityScorer | None = None,
    threshold: float = DUPLICATE_SIMILARITY_THRESHOLD,
    ac_texts: list[str] | None = None,
) -> tuple[bool, float, str | None]:
    """Return whether draft duplicates an existing case (title/workflow/expected)."""
    if not existing:
        return False, 0.0, None

    scorer = scorer or FeatureSimilarityScorer()
    candidate = ScenarioText.from_parts(
        title=draft.title,
        steps=list(draft.steps),
        expected_results=list(draft.expected_results),
        ac_texts=ac_texts or [],
        key="draft",
    )

    best_score = 0.0
    best_key: str | None = None
    for item in existing:
        if isinstance(item, TestCase):
            other = ScenarioText.from_parts(
                title=item.title,
                steps=list(item.steps),
                expected_results=list(item.expected_results),
                ac_texts=ac_texts or [],
                key=f"batch:{item.title}",
            )
            label = item.title
        else:
            other = ScenarioText.from_parts(
                title=item.title,
                steps=list(item.steps),
                expected_results=list(item.expected_results),
                ac_texts=ac_texts or [],
                source_id=item.id,
                key=f"tc:{item.id}",
            )
            label = f"#{item.id} {item.title}"

        # Exact normalized title is always a duplicate.
        if _norm_title(draft.title) == _norm_title(item.title):
            return True, 1.0, label

        score = scorer.score(candidate, other)
        if score > best_score:
            best_score = score
            best_key = label

    if best_score >= threshold and best_key is not None:
        return True, best_score, best_key
    return False, best_score, None


def find_intra_batch_duplicates(
    drafts: list[TestCase],
    *,
    scorer: SimilarityScorer | None = None,
    threshold: float = DUPLICATE_SIMILARITY_THRESHOLD,
) -> dict[int, int]:
    """Map later draft index → earlier duplicate index within the same batch."""
    scorer = scorer or FeatureSimilarityScorer()
    duplicates: dict[int, int] = {}
    seen_titles: dict[str, int] = {}

    for index, draft in enumerate(drafts):
        title_key = _norm_title(draft.title)
        if title_key in seen_titles:
            duplicates[index] = seen_titles[title_key]
            continue

        prior = drafts[:index]
        is_dup, _, _ = is_duplicate_of_existing(
            draft,
            prior,
            scorer=scorer,
            threshold=threshold,
        )
        if is_dup:
            # Find first matching prior index for reporting.
            for prior_index, prior_draft in enumerate(prior):
                hit, _, _ = is_duplicate_of_existing(
                    draft,
                    [prior_draft],
                    scorer=scorer,
                    threshold=threshold,
                )
                if hit:
                    duplicates[index] = prior_index
                    break
        else:
            seen_titles[title_key] = index

    return duplicates


def _norm_title(title: str) -> str:
    return " ".join(title.lower().split())
