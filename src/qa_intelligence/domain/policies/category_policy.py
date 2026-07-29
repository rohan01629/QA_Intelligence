"""QA category applicability policy."""

from __future__ import annotations

from qa_intelligence.domain.enums import (
    ALWAYS_TEST_CATEGORIES,
    FeatureType,
    TestCategory,
)
from qa_intelligence.domain.models.user_story import UserStory
from qa_intelligence.domain.policies.signals import contains_any_positive, story_corpus

OPTIONAL_CATEGORIES: tuple[TestCategory, ...] = (
    TestCategory.BOUNDARY,
    TestCategory.UI,
    TestCategory.API,
    TestCategory.DATABASE,
    TestCategory.INTEGRATION,
    TestCategory.SECURITY,
    TestCategory.ACCESSIBILITY,
    TestCategory.PERFORMANCE,
    TestCategory.COMPATIBILITY,
    TestCategory.PERMISSION,
    TestCategory.LOCALIZATION,
    TestCategory.BUSINESS_RULES,
    TestCategory.STATE_TRANSITION,
    TestCategory.RECOVERY,
    TestCategory.CONCURRENCY,
    TestCategory.CONFIGURATION,
    TestCategory.FEATURE_FLAGS,
    TestCategory.NOTIFICATIONS,
    TestCategory.REPORTING,
    TestCategory.FILE_UPLOAD,
    TestCategory.LOGGING,
    TestCategory.AUDIT,
)

_CATEGORY_SIGNALS: dict[TestCategory, tuple[str, ...]] = {
    TestCategory.BOUNDARY: ("boundary", "min value", "max value", "limit", "range"),
    TestCategory.UI: ("ui", "screen", "button", "page", "frontend", "click", "modal"),
    TestCategory.API: (
        "api",
        "endpoint",
        "rest",
        "http",
        "payload",
        "status code",
        "graphql",
        "backend",
    ),
    TestCategory.DATABASE: (
        "database",
        "sql",
        "schema",
        "migration",
        "table",
        "persistence",
    ),
    TestCategory.INTEGRATION: (
        "integration",
        "downstream",
        "upstream",
        "webhook",
        "third-party",
        "third party",
        "service bus",
        "kafka",
    ),
    TestCategory.SECURITY: ("security", "xss", "csrf", "injection", "secret", "encrypt"),
    TestCategory.ACCESSIBILITY: (
        "accessibility",
        "wcag",
        "screen reader",
        "aria",
        "keyboard navigation",
    ),
    TestCategory.PERFORMANCE: (
        "performance",
        "latency",
        "throughput",
        "load test",
        "sla",
        "p95",
    ),
    TestCategory.COMPATIBILITY: ("browser", "compatible", "safari", "firefox", "chrome version"),
    TestCategory.PERMISSION: ("permission", "rbac", "role", "access denied", "authorize"),
    TestCategory.LOCALIZATION: ("localization", "i18n", "l10n", "locale", "translation"),
    TestCategory.BUSINESS_RULES: ("business rule", "policy engine"),
    TestCategory.STATE_TRANSITION: ("state transition", "status changes", "state machine"),
    TestCategory.RECOVERY: ("retry", "recovery", "failover", "rollback"),
    TestCategory.CONCURRENCY: ("concurrent", "race condition", "parallel", "locking"),
    TestCategory.CONFIGURATION: ("configuration", "config flag", "settings"),
    TestCategory.FEATURE_FLAGS: ("feature flag", "feature toggle"),
    TestCategory.NOTIFICATIONS: ("notification", "email alert", "push notification", "sms"),
    TestCategory.REPORTING: ("report", "dashboard", "analytics"),
    TestCategory.FILE_UPLOAD: ("upload", "attachment", "multipart", "mime"),
    TestCategory.LOGGING: ("logging", "log event"),
    TestCategory.AUDIT: ("audit trail", "audit log", "compliance audit"),
}

_DEFAULT_EXCLUSION_REASONS: dict[TestCategory, str] = {
    TestCategory.UI: "No UI surface change signals found",
    TestCategory.ACCESSIBILITY: "No accessibility or UI interaction signals found",
    TestCategory.DATABASE: "No database or persistence behavior change stated",
    TestCategory.PERFORMANCE: "No performance, load, or SLA requirement stated",
    TestCategory.SECURITY: "No security-specific signals found",
    TestCategory.COMPATIBILITY: "No cross-client compatibility signals found",
    TestCategory.PERMISSION: "No permission or RBAC signals found",
    TestCategory.LOCALIZATION: "No localization signals found",
    TestCategory.FILE_UPLOAD: "No file upload signals found",
    TestCategory.NOTIFICATIONS: "No notification signals found",
    TestCategory.REPORTING: "No reporting signals found",
    TestCategory.FEATURE_FLAGS: "No feature-flag signals found",
    TestCategory.CONFIGURATION: "No configuration signals found",
    TestCategory.CONCURRENCY: "No concurrency signals found",
    TestCategory.RECOVERY: "No recovery/failover signals found",
    TestCategory.STATE_TRANSITION: "No state-transition signals found",
    TestCategory.BOUNDARY: "No boundary-value signals found",
    TestCategory.BUSINESS_RULES: "No distinct business-rule category signals beyond core validation",
    TestCategory.LOGGING: "No logging requirement signals found",
    TestCategory.AUDIT: "No audit requirement signals found",
    TestCategory.API: "No API contract signals found",
    TestCategory.INTEGRATION: "No cross-service integration signals found",
}


def _feature_type_defaults(feature_type: FeatureType) -> set[TestCategory]:
    if feature_type in {FeatureType.BACKEND_API, FeatureType.API}:
        return {TestCategory.API, TestCategory.INTEGRATION}
    if feature_type == FeatureType.UI:
        return {TestCategory.UI}
    if feature_type == FeatureType.INTEGRATION:
        return {TestCategory.INTEGRATION, TestCategory.API}
    if feature_type == FeatureType.DATA:
        return {TestCategory.DATABASE}
    if feature_type == FeatureType.REPORTING:
        return {TestCategory.REPORTING}
    if feature_type == FeatureType.WORKFLOW:
        return {TestCategory.STATE_TRANSITION}
    return set()


def evaluate_categories(
    story: UserStory,
    feature_type: FeatureType,
) -> tuple[list[TestCategory], dict[TestCategory, str], str]:
    """Return (applicable_optional, exclusion_reasons, narrative_reason)."""
    corpus = f" {story_corpus(story)} "
    defaults = _feature_type_defaults(feature_type)
    applicable: list[TestCategory] = []
    exclusion_reasons: dict[TestCategory, str] = {}

    for category in OPTIONAL_CATEGORIES:
        signal_hit = contains_any_positive(corpus, _CATEGORY_SIGNALS.get(category, ()))
        default_hit = category in defaults

        # Backend/API stories must not pull UI/A11y from weak defaults.
        if feature_type in {FeatureType.BACKEND_API, FeatureType.API} and category in {
            TestCategory.UI,
            TestCategory.ACCESSIBILITY,
        }:
            default_hit = False

        if signal_hit or default_hit:
            applicable.append(category)
        else:
            exclusion_reasons[category] = _DEFAULT_EXCLUSION_REASONS.get(
                category,
                f"No {category.display_name} signals found in the user story",
            )

    narrative = _build_reason(feature_type, applicable, exclusion_reasons)
    return applicable, exclusion_reasons, narrative


def always_categories_ordered() -> list[TestCategory]:
    order = (
        TestCategory.POSITIVE,
        TestCategory.NEGATIVE,
        TestCategory.EDGE,
        TestCategory.VALIDATION,
        TestCategory.REGRESSION,
    )
    return [category for category in order if category in ALWAYS_TEST_CATEGORIES]


def _build_reason(
    feature_type: FeatureType,
    applicable: list[TestCategory],
    exclusions: dict[TestCategory, str],
) -> str:
    if feature_type == FeatureType.BACKEND_API:
        core_skips = {
            TestCategory.UI,
            TestCategory.ACCESSIBILITY,
            TestCategory.DATABASE,
            TestCategory.PERFORMANCE,
        }
        if core_skips.issubset(exclusions.keys()):
            return (
                "This user story modifies only backend API behavior "
                "without UI or database changes."
            )
    applicable_names = ", ".join(c.display_name for c in applicable) or "none"
    return (
        f"Feature type is {feature_type.display_name}. "
        f"Applicable optional categories: {applicable_names}."
    )
