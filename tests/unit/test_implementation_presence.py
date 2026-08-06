"""Unit tests for Rule 12 implementation presence (strict AC marker match)."""

from __future__ import annotations

from qa_intelligence.domain.enums import (
    FeatureType,
    GenerationDirective,
    RiskLevel,
    TestCategory,
)
from qa_intelligence.domain.models.code_intelligence import (
    AffectedFile,
    CodeArtifactRole,
    ImplementationSummary,
)
from qa_intelligence.domain.models.generation import GenerationMode
from qa_intelligence.domain.models.qa_strategy import CoverageEstimates, QAStrategy
from qa_intelligence.domain.models.test_strategy import (
    CategoryDecision,
    RiskBasedTestingStrategy,
    TestStrategy,
)
from qa_intelligence.domain.models.user_story import AcceptanceCriteria, UserStory
from qa_intelligence.domain.policies.implementation_presence import (
    assess_presence_across_summaries,
    assess_summary_presence,
    required_implementation_markers,
)
from qa_intelligence.domain.policies.product_rules import CORE_CATEGORIES_ORDERED, PRODUCT_RULES
from qa_intelligence.services.test_case_generation_service import TestCaseGenerationService


def _ascii_story() -> UserStory:
    return UserStory(
        id=116559,
        title="FracPro Live+ - Reports- Rename Download ASCII Report button and launch ASCII Report dialog",
        acceptance_criteria=[
            AcceptanceCriteria(
                order=1,
                text=(
                    'Rename the "Download ASCII Report" button to "ASCII Report" . '
                    "Clicking the ASCII Report button shall not invoke the COMMAND API. "
                    "Clicking the button shall open the ASCII Report modal dialog. "
                    "The dialog shall contain two tabs: Real-time FrPro "
                    "The dialog shall contain two action buttons: Generate Cancel "
                    "Clicking Cancel or closing the dialog shall dismiss the dialog "
                    "without saving any changes."
                ),
                id="AC-1",
            )
        ],
    )


def test_product_rules_include_rule_12() -> None:
    assert len(PRODUCT_RULES) == 13
    assert "not implemented" in PRODUCT_RULES[11].lower() or "do not generate" in PRODUCT_RULES[11].lower()


def test_ascii_story_requires_new_label_and_dialog_markers() -> None:
    markers = required_implementation_markers(_ascii_story())
    assert any(m.startswith("rename_to:ASCII Report") for m in markers)
    assert "struct:dialog" in markers
    assert "struct:realtime_tab" in markers
    assert "struct:frpro_tab" in markers
    assert "struct:generate_action" in markers
    assert "struct:cancel_action" in markers
    # Old label must not be required as present.
    assert not any(m == 'quote:Download ASCII Report' for m in markers)


def test_legacy_ascii_download_is_not_feature_found() -> None:
    """Related report-buttons code without rename/dialog must block generation."""
    story = _ascii_story()
    summary = ImplementationSummary(
        feature=story.title,
        repository_path=r"D:\Live_Plus_UAT",
        affected_files=[
            AffectedFile(
                path="fracpro-agile/src/app/pages/plots/report/report-buttons/report-buttons.component.ts",
                role=CodeArtifactRole.COMPONENT,
                score=1.0,
                reason="matched: ascii, download",
            )
        ],
    )
    legacy = {
        "fracpro-agile/src/app/pages/plots/report/report-buttons/report-buttons.component.ts": (
            'buttonPrefixAscii = "DOWNLOAD_ASCII_REPORT";\n'
            'generateAscii = "GenerateASCII";\n'
            "onGenerateAsciiFile() { this.callSignalR('GenerateASCII'); }\n"
        )
    }
    presence = assess_summary_presence(summary, story, file_contents=legacy)
    assert presence.found is False
    assert presence.missing_markers


def test_implemented_ascii_dialog_is_feature_found() -> None:
    story = _ascii_story()
    summary = ImplementationSummary(
        feature=story.title,
        repository_path=r"D:\Live_Plus_UAT",
        affected_files=[
            AffectedFile(
                path="report-buttons.component.ts",
                role=CodeArtifactRole.COMPONENT,
                score=1.0,
                reason="matched: ascii",
            )
        ],
    )
    implemented = {
        "report-buttons.component.ts": (
            'buttonPrefixAscii = "ASCII_REPORT"; // ASCII Report\n'
            "openAsciiDialog() { this.dialog.open(AsciiReportDialog); }\n"
            "tabs: Real-time, FrPro\n"
            "Generate Cancel buttons on modal dialog\n"
            "asciirealtime asciifp\n"
        )
    }
    presence = assess_summary_presence(summary, story, file_contents=implemented)
    assert presence.found is True


def test_any_codebase_sufficient_when_implemented() -> None:
    story = UserStory(
        id=2,
        title="Magenta Circle on LogLog Plot",
        acceptance_criteria=[
            AcceptanceCriteria(
                order=1,
                text='Display a "magenta circle" on the LogLog dialog plot',
                id="1",
            )
        ],
    )
    miss = ImplementationSummary(
        feature=story.title,
        repository_path=r"D:\Live_Plus_UAT",
        affected_files=[
            AffectedFile(path="auth.ts", role=CodeArtifactRole.SERVICE, score=0.2, reason="x")
        ],
    )
    hit = ImplementationSummary(
        feature=story.title,
        repository_path=r"C:\Minifrac\fracpro-agile",
        affected_files=[
            AffectedFile(
                path="loglog.component.ts",
                role=CodeArtifactRole.COMPONENT,
                score=0.9,
                reason="matched",
            )
        ],
    )
    presence = assess_presence_across_summaries(
        [miss, hit],
        story,
        file_contents_by_repo={
            miss.repository_path: {"auth.ts": "login only"},
            hit.repository_path: {
                "loglog.component.ts": 'draw "magenta circle" on LogLog dialog plot'
            },
        },
    )
    assert presence.found is True


def test_generation_blocked_when_feature_not_found() -> None:
    categories = list(CORE_CATEGORIES_ORDERED)
    qa = QAStrategy(
        feature_type=FeatureType.UI,
        risk=RiskLevel.MEDIUM,
        testing_required=categories,
        testing_not_required=[],
        reason="UI",
        estimates=CoverageEstimates(estimated_new_test_cases=25, preliminary=False),
    )
    strategy = TestStrategy(
        user_story_id=99,
        feature_type=FeatureType.UI,
        risk_level=RiskLevel.MEDIUM,
        applicable_categories=[
            CategoryDecision(category=c, applicable=True, reason="x") for c in categories
        ],
        skipped_categories=[],
        estimated_new_test_cases=25,
        risk_based_strategy=RiskBasedTestingStrategy(
            risk_level=RiskLevel.MEDIUM,
            depth_guidance="x",
            regression_emphasis="x",
            priority_order=categories,
        ),
        narrative_summary="x",
        generation_directive=GenerationDirective.FRESH_SUITE,
        estimates=qa.estimates,
        qa_strategy=qa,
    )
    story = UserStory(
        id=99,
        title="Quantum Nebula Flux",
        acceptance_criteria=[AcceptanceCriteria(order=1, text='Enable "Nebula Flux"', id="1")],
    )
    summary = ImplementationSummary(
        feature=story.title,
        repository_path=r"D:\Live_Plus_UAT",
        feature_found=False,
        feature_presence_notes="missing markers",
        related_implementation_available=True,
        related_implementation_notes="legacy path",
        related_file_paths=["report-buttons.component.ts"],
        affected_files=[],
    )
    result = TestCaseGenerationService().generate(
        strategy,
        story,
        implementation_summary=summary,
    )
    assert result.blocked is True
    assert result.mode == GenerationMode.BLOCKED
    assert result.generated == []
    assert "ask the user" in result.notes.lower() or "related" in result.notes.lower()


def test_generation_allowed_when_user_approves_related() -> None:
    categories = list(CORE_CATEGORIES_ORDERED)
    qa = QAStrategy(
        feature_type=FeatureType.UI,
        risk=RiskLevel.MEDIUM,
        testing_required=categories,
        testing_not_required=[],
        reason="UI",
        estimates=CoverageEstimates(estimated_new_test_cases=5, preliminary=False),
    )
    strategy = TestStrategy(
        user_story_id=99,
        feature_type=FeatureType.UI,
        risk_level=RiskLevel.MEDIUM,
        applicable_categories=[
            CategoryDecision(category=c, applicable=True, reason="x") for c in categories
        ],
        skipped_categories=[],
        estimated_new_test_cases=5,
        risk_based_strategy=RiskBasedTestingStrategy(
            risk_level=RiskLevel.MEDIUM,
            depth_guidance="x",
            regression_emphasis="x",
            priority_order=categories,
        ),
        narrative_summary="x",
        generation_directive=GenerationDirective.FRESH_SUITE,
        estimates=qa.estimates,
        qa_strategy=qa,
    )
    story = UserStory(
        id=99,
        title="ASCII Report dialog",
        acceptance_criteria=[
            AcceptanceCriteria(order=1, text='Rename to "ASCII Report" and open dialog', id="1")
        ],
    )
    summary = ImplementationSummary(
        feature=story.title,
        repository_path=r"D:\Live_Plus_UAT",
        feature_found=False,
        related_implementation_available=True,
        related_file_paths=["report-buttons.component.ts"],
        affected_files=[
            AffectedFile(
                path="report-buttons.component.ts",
                role=CodeArtifactRole.COMPONENT,
                score=0.9,
                reason="matched: ascii",
            )
        ],
    )
    result = TestCaseGenerationService().generate(
        strategy,
        story,
        implementation_summary=summary,
        allow_related_implementation=True,
    )
    assert result.blocked is False
    assert result.generated
