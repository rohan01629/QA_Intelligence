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
RULE_11_GENERATION_VOLUME = (
    "Fresh/full generation: produce at least 25 test cases for typical stories. "
    "Expand to 50–60 only when the story is complex (high/critical risk, multiple "
    "AC items, many Scenario N blocks, or long AC text). Short/simple stories "
    "must stay near 25 — do not pad to 50 with generic cases."
)
RULE_12_REQUIRE_IMPLEMENTATION = (
    "If the User Story feature is not implemented in any configured local "
    "application codebase, do not generate test cases by default. First analyze "
    "previous/related implementation in the existing codebases and report it. "
    "Generation from related/legacy code is optional — ask the user whether to "
    "proceed based on that related implementation before generating. Only "
    "generate without asking when the story feature itself is found, or when "
    "the user explicitly approves related-implementation generation."
)
RULE_13_CATEGORY_MIX = (
    "When generating the suite, decide which test cases are Regression "
    "(~30% — adjacent/stability) and which are Critical/Sanity (~10% — high risk / "
    "business impact), draft each case for that role, then mark "
    "Custom.IsRegression / Custom.Sanity from that decision. Do not put "
    "'Regression' or 'Critical' in the title; report TC numbers in the generation "
    "summary, then link created Test Cases to the User Story."
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
    RULE_11_GENERATION_VOLUME,
    RULE_12_REQUIRE_IMPLEMENTATION,
    RULE_13_CATEGORY_MIX,
)

# Rule 11 — generation volume bounds (fresh suite / full generation).
MIN_GENERATED_TEST_CASES: int = 25
TARGET_COMPLEX_TEST_CASES: int = 50
MAX_GENERATED_TEST_CASES: int = 60

# Rule 13 — mix ratios of the generated suite.
REGRESSION_MIX_RATIO: float = 0.30
CRITICAL_MIX_RATIO: float = 0.10

# Rule 5 — core / always-on categories (display order).
CORE_CATEGORIES_ORDERED: tuple[TestCategory, ...] = (
    TestCategory.POSITIVE,
    TestCategory.NEGATIVE,
    TestCategory.EDGE,
    TestCategory.VALIDATION,
    TestCategory.REGRESSION,
)

assert set(CORE_CATEGORIES_ORDERED) == set(ALWAYS_TEST_CATEGORIES)

# Allowed public fields on a generated / submitted test case (Rule 8 content + Rule 13 ADO mix).
TEST_CASE_CONTENT_FIELDS: frozenset[str] = frozenset(
    {"title", "steps", "expected_results"}
)
TEST_CASE_ADO_MIX_FIELDS: frozenset[str] = frozenset({"is_regression", "is_sanity"})
TEST_CASE_ALLOWED_FIELDS: frozenset[str] = (
    TEST_CASE_CONTENT_FIELDS | TEST_CASE_ADO_MIX_FIELDS
)

# Similarity threshold for Rule 1 duplicate rejection against inventory / batch.
DUPLICATE_SIMILARITY_THRESHOLD: float = 0.82


def product_rules_text() -> str:
    """Human-readable numbered rule list for prompts / MCP guidance."""
    lines = [f"Rule {index}: {rule}" for index, rule in enumerate(PRODUCT_RULES, start=1)]
    return "\n".join(lines)
