"""Risk level scoring policy."""

from __future__ import annotations

from qa_intelligence.domain.enums import FeatureType, RiskLevel
from qa_intelligence.domain.models.user_story import UserStory
from qa_intelligence.domain.policies.signals import contains_any, story_corpus

_CRITICAL = (
    "pii",
    "payment",
    "pci",
    "security breach",
    "authentication bypass",
    "authorization bypass",
    "gdpr",
    "hipaa",
)
_HIGH = (
    "breaking change",
    "production",
    "migrate",
    "migration",
    "contract change",
    "backward compatible",
    "high risk",
    "critical path",
    "revenue",
)
_LOW = (
    "typo",
    "cosmetic",
    "documentation",
    "readme",
    "wording",
    "copy change",
)


def classify_risk(
    story: UserStory,
    feature_type: FeatureType,
) -> RiskLevel:
    corpus = story_corpus(story)
    if contains_any(corpus, _CRITICAL):
        return RiskLevel.CRITICAL
    if contains_any(corpus, _HIGH):
        return RiskLevel.HIGH
    if contains_any(corpus, _LOW) and len(story.acceptance_criteria) <= 1:
        return RiskLevel.LOW

    # Feature-type defaults
    if feature_type in {
        FeatureType.BACKEND_API,
        FeatureType.API,
        FeatureType.INTEGRATION,
        FeatureType.DATA,
    }:
        return RiskLevel.HIGH if len(story.acceptance_criteria) >= 1 else RiskLevel.MEDIUM
    if feature_type == FeatureType.UI:
        return RiskLevel.MEDIUM
    if feature_type == FeatureType.REPORTING:
        return RiskLevel.MEDIUM
    return RiskLevel.MEDIUM
