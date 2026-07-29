"""Canonical product rules for QA Intelligence.

These rules are mandatory. Services must enforce them; they are not optional guidance.
"""

from __future__ import annotations

from qa_intelligence.domain.enums import ALWAYS_TEST_CATEGORIES, TestCategory

# ---------------------------------------------------------------------------
# Rule catalog (stable identifiers)
# ---------------------------------------------------------------------------

RULE_1_NO_DUPLICATES = (
    "Never generate duplicate test cases."
)
RULE_2_FRESH_SUITE = (
    "If no existing test cases exist, generate a fresh test suite."
)
RULE_3_MISSING_ONLY = (
    "If existing test cases exist, generate only missing scenarios."
)
RULE_4_ANALYZE_BEFORE_CATEGORIES = (
    "Always analyze the User Story before selecting test categories."
)
RULE_5_CORE_CATEGORIES = (
    "Core categories: Positive, Negative, Edge Cases, Validation, Regression."
)
RULE_6_OPTIONAL_WHEN_APPLICABLE = (
    "Optional categories are included only when applicable."
)
RULE_7_STEP_RESULT_PAIRITY = (
    "Every test step must have exactly one corresponding expected result."
)
RULE_8_THREE_FIELDS_ONLY = (
    "Each test case contains only: Test Title, Test Steps, Expected Results."
)
RULE_9_REJECT_STEP_MISMATCH = (
    "Reject invalid output where the number of steps and expected results differ."
)
RULE_10_NO_INFERRED_REQUIREMENTS = (
    "Never infer requirements that are not present. Report requirement gaps instead."
)

PRODUCT_RULES: tuple[str, ...] = (
    RULE_1_NO_DUPLICATES,
    RULE_2_FRESH_SUITE,
    RULE_3_MISSING_ONLY,
    RULE_4_ANALYZE_BEFORE_CATEGORIES,
    RULE_5_CORE_CATEGORIES,
    RULE_6_OPTIONAL_WHEN_APPLICABLE,
    RULE_7_STEP_RESULT_PAIRITY,
    RULE_8_THREE_FIELDS_ONLY,
    RULE_9_REJECT_STEP_MISMATCH,
    RULE_10_NO_INFERRED_REQUIREMENTS,
)

# Rule 5 — core / always-on categories (display order).
CORE_CATEGORIES_ORDERED: tuple[TestCategory, ...] = (
    TestCategory.POSITIVE,
    TestCategory.NEGATIVE,
    TestCategory.EDGE,
    TestCategory.VALIDATION,
    TestCategory.REGRESSION,
)

assert set(CORE_CATEGORIES_ORDERED) == set(ALWAYS_TEST_CATEGORIES)

# Allowed public fields on a generated / submitted test case (Rule 8).
TEST_CASE_ALLOWED_FIELDS: frozenset[str] = frozenset(
    {"title", "steps", "expected_results"}
)

# Similarity threshold for Rule 1 duplicate rejection against inventory / batch.
DUPLICATE_SIMILARITY_THRESHOLD: float = 0.82


def product_rules_text() -> str:
    """Human-readable numbered rule list for prompts / MCP guidance."""
    lines = [f"Rule {index}: {rule}" for index, rule in enumerate(PRODUCT_RULES, start=1)]
    return "\n".join(lines)
