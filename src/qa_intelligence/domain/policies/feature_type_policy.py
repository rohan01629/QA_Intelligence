"""Feature type classification policy (deterministic signals)."""

from __future__ import annotations

from qa_intelligence.domain.enums import FeatureType
from qa_intelligence.domain.policies.signals import contains_any_positive, story_corpus
from qa_intelligence.domain.models.user_story import UserStory

_BACKEND_API = (
    "backend api",
    "backend",
    "rest api",
    "rest endpoint",
    "http endpoint",
    "api endpoint",
    "status code",
    "request payload",
    "response payload",
    "openapi",
    "swagger",
)
_UI = (
    "user interface",
    "screen",
    "button",
    "page layout",
    "click",
    "dropdown",
    "modal",
    "css",
    "frontend",
    "react",
    "angular",
    "ui",
)
_API = (
    "endpoint",
    "rest",
    "graphql",
    "http",
    "api",
    "payload",
    "json body",
    "status code",
)
_INTEGRATION = (
    "integration",
    "webhook",
    "downstream",
    "upstream",
    "third-party",
    "third party",
    "event bus",
    "message queue",
    "kafka",
    "service bus",
)
_WORKFLOW = (
    "workflow",
    "state machine",
    "approval flow",
    "state transition",
    "orchestration",
)
_DATA = (
    "database schema",
    "migration",
    "etl",
    "dataset",
    "data pipeline",
    "persistence",
)
_REPORTING = (
    "report",
    "dashboard",
    "analytics export",
    "csv export",
)


def classify_feature_type(story: UserStory) -> tuple[FeatureType, str]:
    """Return feature type and short rationale."""
    corpus = f" {story_corpus(story)} "

    scores: dict[FeatureType, int] = {
        FeatureType.BACKEND_API: 0,
        FeatureType.UI: 0,
        FeatureType.API: 0,
        FeatureType.INTEGRATION: 0,
        FeatureType.WORKFLOW: 0,
        FeatureType.DATA: 0,
        FeatureType.REPORTING: 0,
        FeatureType.OTHER: 0,
    }

    if contains_any_positive(corpus, _BACKEND_API):
        scores[FeatureType.BACKEND_API] += 3
    if contains_any_positive(corpus, _API):
        scores[FeatureType.API] += 2
        scores[FeatureType.BACKEND_API] += 1
    if contains_any_positive(corpus, _UI):
        scores[FeatureType.UI] += 3
    if contains_any_positive(corpus, _INTEGRATION):
        scores[FeatureType.INTEGRATION] += 3
    if contains_any_positive(corpus, _WORKFLOW):
        scores[FeatureType.WORKFLOW] += 3
    if contains_any_positive(corpus, _DATA):
        scores[FeatureType.DATA] += 3
    if contains_any_positive(corpus, _REPORTING):
        scores[FeatureType.REPORTING] += 3

    # Prefer BACKEND_API when API signals dominate and UI is absent.
    if scores[FeatureType.BACKEND_API] >= 2 and scores[FeatureType.UI] == 0:
        scores[FeatureType.BACKEND_API] += 2

    best = max(scores, key=lambda key: scores[key])
    if scores[best] == 0:
        return FeatureType.OTHER, "No strong feature signals found; classified as Other."

    return best, f"Classified as {best.display_name} based on requirement signals."
