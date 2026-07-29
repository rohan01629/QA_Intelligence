"""Domain enumerations for QA Intelligence."""

from __future__ import annotations

from enum import StrEnum


class FeatureType(StrEnum):
    """Classification of the change under test."""

    BACKEND_API = "backend_api"
    UI = "ui"
    API = "api"
    WORKFLOW = "workflow"
    DATA = "data"
    INTEGRATION = "integration"
    REPORTING = "reporting"
    OTHER = "other"

    @property
    def display_name(self) -> str:
        labels = {
            FeatureType.BACKEND_API: "Backend API",
            FeatureType.UI: "UI",
            FeatureType.API: "API",
            FeatureType.WORKFLOW: "Workflow",
            FeatureType.DATA: "Data",
            FeatureType.INTEGRATION: "Integration",
            FeatureType.REPORTING: "Reporting",
            FeatureType.OTHER: "Other",
        }
        return labels[self]


class RiskLevel(StrEnum):
    """Business / technical risk of the user story."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def display_name(self) -> str:
        return self.value.capitalize()


class RequirementGapType(StrEnum):
    """Kinds of incompleteness detected in requirements."""

    MISSING_VALIDATION = "missing_validation"
    AMBIGUOUS_AC = "ambiguous_ac"
    MISSING_EXPECTED_BEHAVIOR = "missing_expected_behavior"
    MISSING_ERROR_HANDLING = "missing_error_handling"
    CONFLICTING_REQUIREMENTS = "conflicting_requirements"
    OTHER = "other"


class GapSeverity(StrEnum):
    """Severity of a requirement gap."""

    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"


class TestCategory(StrEnum):
    """Always-on and optional test categories."""

    __test__ = False

    # Always
    POSITIVE = "positive"
    NEGATIVE = "negative"
    EDGE = "edge"
    VALIDATION = "validation"
    REGRESSION = "regression"
    # Optional
    BOUNDARY = "boundary"
    UI = "ui"
    API = "api"
    DATABASE = "database"
    INTEGRATION = "integration"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    COMPATIBILITY = "compatibility"
    PERMISSION = "permission"
    LOCALIZATION = "localization"
    BUSINESS_RULES = "business_rules"
    STATE_TRANSITION = "state_transition"
    RECOVERY = "recovery"
    CONCURRENCY = "concurrency"
    CONFIGURATION = "configuration"
    FEATURE_FLAGS = "feature_flags"
    NOTIFICATIONS = "notifications"
    REPORTING = "reporting"
    FILE_UPLOAD = "file_upload"
    LOGGING = "logging"
    AUDIT = "audit"

    @property
    def display_name(self) -> str:
        labels = {
            TestCategory.POSITIVE: "Positive",
            TestCategory.NEGATIVE: "Negative",
            TestCategory.EDGE: "Edge Cases",
            TestCategory.VALIDATION: "Validation",
            TestCategory.REGRESSION: "Regression",
            TestCategory.BOUNDARY: "Boundary Value Analysis",
            TestCategory.UI: "UI",
            TestCategory.API: "API",
            TestCategory.DATABASE: "Database",
            TestCategory.INTEGRATION: "Integration",
            TestCategory.SECURITY: "Security",
            TestCategory.ACCESSIBILITY: "Accessibility",
            TestCategory.PERFORMANCE: "Performance",
            TestCategory.COMPATIBILITY: "Compatibility",
            TestCategory.PERMISSION: "Permission",
            TestCategory.LOCALIZATION: "Localization",
            TestCategory.BUSINESS_RULES: "Business Rules",
            TestCategory.STATE_TRANSITION: "State Transition",
            TestCategory.RECOVERY: "Recovery",
            TestCategory.CONCURRENCY: "Concurrency",
            TestCategory.CONFIGURATION: "Configuration",
            TestCategory.FEATURE_FLAGS: "Feature Flags",
            TestCategory.NOTIFICATIONS: "Notifications",
            TestCategory.REPORTING: "Reporting",
            TestCategory.FILE_UPLOAD: "File Upload",
            TestCategory.LOGGING: "Logging",
            TestCategory.AUDIT: "Audit",
        }
        return labels[self]


ALWAYS_TEST_CATEGORIES: frozenset[TestCategory] = frozenset(
    {
        TestCategory.POSITIVE,
        TestCategory.NEGATIVE,
        TestCategory.EDGE,
        TestCategory.VALIDATION,
        TestCategory.REGRESSION,
    }
)


class GenerationDirective(StrEnum):
    """How Cursor should treat test-case generation for a story."""

    FRESH_SUITE = "fresh_suite"
    GAP_FILL_ONLY = "gap_fill_only"
    BLOCKED = "blocked"


class DuplicateBasis(StrEnum):
    """Why two scenarios are considered duplicates."""

    INTENT = "intent"
    WORKFLOW = "workflow"
    AC_MAPPING = "ac_mapping"
    EXPECTED_RESULT = "expected_result"


class ScenarioSource(StrEnum):
    """Origin of a scenario reference in coverage analysis."""

    EXISTING = "existing"
    SIMILAR = "similar"
    BUG = "bug"
    MISSING = "missing"
    DRAFT = "draft"


class CreateStatus(StrEnum):
    """Per-item outcome when creating test cases."""

    CREATED = "created"
    VALIDATED_ONLY = "validated_only"
    REJECTED = "rejected"


class LinkStatus(StrEnum):
    """Per-item outcome when linking test cases."""

    LINKED = "linked"
    SKIPPED = "skipped"
    FAILED = "failed"


class ScenarioDisposition(StrEnum):
    """Classification of a scenario relative to the user story and inventory."""

    DUPLICATE = "duplicate"
    COVERED = "covered"
    NEEDS_UPDATE = "needs_update"
    GENERATE_NEW = "generate_new"
