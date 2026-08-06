"""Deterministic test-case draft templates by category.

Every template returns equal-length steps and expected_results.
"""

from __future__ import annotations

from qa_intelligence.domain.enums import FeatureType, TestCategory


def build_draft(
    *,
    scenario_title: str,
    category: TestCategory,
    feature_type: FeatureType,
    story_title: str,
) -> dict[str, object]:
    """Build a raw 3-field draft for validation."""
    intent = scenario_title.strip().rstrip(".")
    feature = feature_type.display_name
    builder = _TEMPLATE_BUILDERS.get(category, _positive_template)
    title, steps, expected = builder(intent=intent, feature=feature, story_title=story_title)
    return {
        "title": title,
        "steps": steps,
        "expected_results": expected,
    }


def _positive_template(*, intent: str, feature: str, story_title: str) -> tuple[str, list[str], list[str]]:
    title = f"Verify {intent} - Positive"
    steps = [
        f"Prepare a valid precondition for '{story_title}'.",
        f"Execute the {feature} behavior for: {intent}.",
        "Observe the primary outcome.",
    ]
    expected = [
        "Preconditions are ready and valid.",
        f"The {feature} behavior executes without error.",
        f"The outcome satisfies: {intent}.",
    ]
    return title, steps, expected


def _negative_template(*, intent: str, feature: str, story_title: str) -> tuple[str, list[str], list[str]]:
    title = f"Verify {intent} - Negative"
    steps = [
        f"Prepare an invalid or unauthorized condition related to '{story_title}'.",
        f"Attempt the {feature} behavior for: {intent}.",
        "Capture the system response that must block or reject the action.",
    ]
    expected = [
        "Invalid or unauthorized condition is in place.",
        f"The {feature} behavior shall not complete successfully for the invalid path.",
        "An appropriate error or failure response is returned and the action is blocked.",
    ]
    return title, steps, expected


def _edge_template(*, intent: str, feature: str, story_title: str) -> tuple[str, list[str], list[str]]:
    title = f"Verify {intent} - Edge Case"
    steps = [
        "Prepare boundary or unusual input data.",
        f"Execute the {feature} behavior for: {intent}.",
        "Review system handling of the edge input.",
    ]
    expected = [
        "Boundary/unusual input is prepared.",
        f"The {feature} behavior accepts or rejects the edge input per rules.",
        "No unexpected failure or data corruption occurs.",
    ]
    return title, steps, expected


def _validation_template(*, intent: str, feature: str, story_title: str) -> tuple[str, list[str], list[str]]:
    title = f"Verify {intent} - Validation"
    steps = [
        "Prepare input that violates a validation rule.",
        f"Submit the input through the {feature} path for: {intent}.",
        "Inspect validation messaging and status.",
    ]
    expected = [
        "Invalid input is prepared.",
        "Submission is blocked or flagged by validation.",
        "Clear validation feedback is returned.",
    ]
    return title, steps, expected


def _regression_template(*, intent: str, feature: str, story_title: str) -> tuple[str, list[str], list[str]]:
    # Rule 13: regression is tracked via mix metadata — do not put "Regression" in the title.
    title = f"Verify adjacent workflow remains stable for {intent}"
    steps = [
        f"Identify an adjacent previously working workflow impacted by '{story_title}'.",
        "Execute the baseline adjacent workflow unchanged.",
        f"Confirm baseline behavior still holds alongside: {intent}.",
    ]
    expected = [
        "Impacted adjacent workflow is identified.",
        "Adjacent workflow completes successfully with no regression.",
        "Baseline parity still holds relative to the change.",
    ]
    return title, steps, expected


def _api_template(*, intent: str, feature: str, story_title: str) -> tuple[str, list[str], list[str]]:
    title = f"Verify {intent} - API"
    steps = [
        "Prepare a valid API request payload and headers.",
        f"Call the API endpoint related to: {intent}.",
        "Inspect HTTP status code and response body.",
    ]
    expected = [
        "Request payload and headers are valid.",
        "API call is accepted by the service.",
        "Status code and body match the acceptance criterion.",
    ]
    return title, steps, expected


def _integration_template(*, intent: str, feature: str, story_title: str) -> tuple[str, list[str], list[str]]:
    title = f"Verify {intent} - Integration"
    steps = [
        "Prepare upstream/downstream dependency stubs or test data.",
        f"Trigger the integrated flow for: {intent}.",
        "Verify cross-component handoff and final state.",
    ]
    expected = [
        "Dependencies are ready for the integration path.",
        "Integrated flow is triggered successfully.",
        "Downstream/upstream state is consistent with the requirement.",
    ]
    return title, steps, expected


def _ui_template(*, intent: str, feature: str, story_title: str) -> tuple[str, list[str], list[str]]:
    title = f"Verify {intent} - UI"
    steps = [
        "Open the relevant UI screen.",
        f"Perform the user action for: {intent}.",
        "Observe the UI feedback.",
    ]
    expected = [
        "UI screen opens successfully.",
        "User action is accepted by the UI.",
        "UI reflects the expected result for the criterion.",
    ]
    return title, steps, expected


def _generic_optional_template(
    *,
    intent: str,
    feature: str,
    story_title: str,
    category: TestCategory,
) -> tuple[str, list[str], list[str]]:
    label = category.display_name
    title = f"Verify {intent} - {label}"
    steps = [
        f"Prepare conditions required for {label} testing of '{story_title}'.",
        f"Execute the {feature} scenario for: {intent}.",
        f"Evaluate {label} outcome.",
    ]
    expected = [
        f"{label} preconditions are satisfied.",
        f"The {feature} scenario executes.",
        f"{label} expectations for the criterion are met.",
    ]
    return title, steps, expected


_TEMPLATE_BUILDERS = {
    TestCategory.POSITIVE: _positive_template,
    TestCategory.NEGATIVE: _negative_template,
    TestCategory.EDGE: _edge_template,
    TestCategory.VALIDATION: _validation_template,
    TestCategory.REGRESSION: _regression_template,
    TestCategory.API: _api_template,
    TestCategory.INTEGRATION: _integration_template,
    TestCategory.UI: _ui_template,
}


def build_draft_for_category(
    *,
    scenario_title: str,
    category: TestCategory,
    feature_type: FeatureType,
    story_title: str,
    mark_critical: bool = False,
) -> dict[str, object]:
    # ``mark_critical`` is retained for callers but does not alter the title
    # (Rule 13 classifications are reported by TC index/metadata, not title text).
    _ = mark_critical
    if category in _TEMPLATE_BUILDERS:
        return build_draft(
            scenario_title=scenario_title,
            category=category,
            feature_type=feature_type,
            story_title=story_title,
        )
    title, steps, expected = _generic_optional_template(
        intent=scenario_title.strip().rstrip("."),
        feature=feature_type.display_name,
        story_title=story_title,
        category=category,
    )
    return {"title": title, "steps": steps, "expected_results": expected}
