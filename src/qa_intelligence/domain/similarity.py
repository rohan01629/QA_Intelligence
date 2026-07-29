"""Semantic scenario text and similarity scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

# Light stopword set — keeps verbs/objects that carry intent.
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "to",
        "of",
        "and",
        "or",
        "for",
        "in",
        "on",
        "at",
        "by",
        "with",
        "from",
        "is",
        "are",
        "be",
        "as",
        "that",
        "this",
        "it",
        "into",
    }
)

# Intent synonym groups — semantic equivalence beyond exact wording.
_SYNONYM_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"login", "logon", "signin", "sign", "authenticate", "authentication", "auth"}),
    frozenset({"verify", "validate", "ensure", "check", "confirm", "assert"}),
    frozenset({"success", "successful", "successfully", "ok", "pass"}),
    frozenset({"fail", "failure", "failed", "error", "invalid"}),
    frozenset({"create", "add", "insert", "register"}),
    frozenset({"update", "edit", "modify", "change"}),
    frozenset({"delete", "remove", "cancel"}),
    frozenset({"api", "endpoint", "rest", "service"}),
    frozenset({"user", "customer", "account"}),
    frozenset({"password", "credential", "credentials"}),
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class ScenarioText:
    """Normalized textual view of a scenario for semantic scoring."""

    title: str
    steps: tuple[str, ...] = ()
    expected_results: tuple[str, ...] = ()
    ac_tokens: tuple[str, ...] = ()
    source_id: int | None = None
    key: str = ""

    @classmethod
    def from_parts(
        cls,
        *,
        title: str,
        steps: list[str] | None = None,
        expected_results: list[str] | None = None,
        ac_texts: list[str] | None = None,
        source_id: int | None = None,
        key: str = "",
    ) -> ScenarioText:
        return cls(
            title=title or "",
            steps=tuple(steps or []),
            expected_results=tuple(expected_results or []),
            ac_tokens=tuple(tokenize(" ".join(ac_texts or []))),
            source_id=source_id,
            key=key or title,
        )


@runtime_checkable
class SimilarityScorer(Protocol):
    def score(self, left: ScenarioText, right: ScenarioText) -> float:
        """Return similarity in [0.0, 1.0]."""
        ...

    def explain_basis(self, left: ScenarioText, right: ScenarioText) -> str:
        ...


def tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, drop stopwords, map synonyms to canonical form."""
    raw = _TOKEN_RE.findall(text.lower())
    tokens: list[str] = []
    for token in raw:
        if token in _STOPWORDS:
            continue
        tokens.append(_canonicalize(token))
    return tokens


def _canonicalize(token: str) -> str:
    for group in _SYNONYM_GROUPS:
        if token in group:
            # Stable representative: lexicographically smallest member.
            return sorted(group)[0]
    # Light stemming for trailing 's' / 'ing' / 'ed'
    if token.endswith("ing") and len(token) > 5:
        return token[:-3]
    if token.endswith("ed") and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and not token.endswith("ss") and len(token) > 3:
        return token[:-1]
    return token


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    intersection = left.intersection(right)
    union = left.union(right)
    return len(intersection) / len(union)


class FeatureSimilarityScorer:
    """Weighted semantic similarity over title intent, workflow, expected results, AC tokens.

    Weights (architecture v1):
    - title intent: 0.35
    - workflow / steps: 0.35
    - expected results: 0.20
    - AC overlap: 0.10
    """

    TITLE_WEIGHT = 0.35
    WORKFLOW_WEIGHT = 0.35
    EXPECTED_WEIGHT = 0.20
    AC_WEIGHT = 0.10

    def score(self, left: ScenarioText, right: ScenarioText) -> float:
        title = jaccard(set(tokenize(left.title)), set(tokenize(right.title)))
        left_steps = set(tokenize(" ".join(left.steps)))
        right_steps = set(tokenize(" ".join(right.steps)))
        left_expected = set(tokenize(" ".join(left.expected_results)))
        right_expected = set(tokenize(" ".join(right.expected_results)))

        title_w = self.TITLE_WEIGHT
        workflow_w = self.WORKFLOW_WEIGHT
        expected_w = self.EXPECTED_WEIGHT
        ac_w = self.AC_WEIGHT

        # Missing workflow on either side → do not penalize; fold weight into title.
        if not left_steps or not right_steps:
            title_w += workflow_w
            workflow_w = 0.0
            workflow = 0.0
        else:
            workflow = jaccard(left_steps, right_steps)

        # Missing expected on either side → fold into title.
        if not left_expected or not right_expected:
            title_w += expected_w
            expected_w = 0.0
            expected = 0.0
        else:
            expected = jaccard(left_expected, right_expected)

        if not left.ac_tokens or not right.ac_tokens:
            title_w += ac_w
            ac_w = 0.0
            ac = 0.0
        else:
            ac = jaccard(set(left.ac_tokens), set(right.ac_tokens))

        total = (
            title_w * title
            + workflow_w * workflow
            + expected_w * expected
            + ac_w * ac
        )
        return round(min(max(total, 0.0), 1.0), 4)

    def explain_basis(self, left: ScenarioText, right: ScenarioText) -> str:
        title = jaccard(set(tokenize(left.title)), set(tokenize(right.title)))
        left_steps = set(tokenize(" ".join(left.steps)))
        right_steps = set(tokenize(" ".join(right.steps)))
        left_expected = set(tokenize(" ".join(left.expected_results)))
        right_expected = set(tokenize(" ".join(right.expected_results)))
        workflow = (
            jaccard(left_steps, right_steps)
            if left_steps and right_steps
            else 0.0
        )
        expected = (
            jaccard(left_expected, right_expected)
            if left_expected and right_expected
            else 0.0
        )
        parts = [
            f"title={title:.2f}",
            f"workflow={workflow:.2f}",
            f"expected={expected:.2f}",
        ]
        dominant = max(
            ("intent", title),
            ("workflow", workflow),
            ("expected_result", expected),
            key=lambda item: item[1],
        )[0]
        return f"basis={dominant}; " + ", ".join(parts)
