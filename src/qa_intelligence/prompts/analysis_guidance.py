"""Analysis / generation guidance — embeds mandatory product rules."""

from __future__ import annotations

from qa_intelligence.domain.policies.product_rules import product_rules_text


def product_rules_guidance() -> str:
    """Return the numbered product rules for MCP / Cursor consumption."""
    return product_rules_text()


def analysis_guidance() -> str:
    """Short guidance fragment attached to analysis-oriented tool responses."""
    return (
        "Analyze the User Story before selecting categories. "
        "Report requirement gaps; never invent missing acceptance criteria.\n\n"
        + product_rules_text()
    )


def generation_guidance() -> str:
    """Short guidance for generation / create paths."""
    return (
        "Generate a fresh suite only when no existing tests exist; "
        "otherwise generate only missing scenarios. "
        "Fresh/full generation must include at least 25 test cases "
        "(expand to 50–60 when complex; cap at 60). "
        "Never emit duplicates. Each case has only title, steps, expected_results "
        "with equal step and expected-result counts.\n\n"
        + product_rules_text()
    )
