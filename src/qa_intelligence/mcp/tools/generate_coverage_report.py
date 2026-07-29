"""MCP tool: generate_coverage_report."""

from __future__ import annotations

from typing import Any

from qa_intelligence.domain.enums import GenerationDirective, ScenarioSource
from qa_intelligence.domain.models.analysis import RequirementAnalysis
from qa_intelligence.domain.models.coverage import CoverageReport, ScenarioRef
from qa_intelligence.domain.models.coverage_matrix import CoverageStatus
from qa_intelligence.domain.models.qa_strategy import CoverageEstimates
from qa_intelligence.mcp import responses
from qa_intelligence.mcp.parsers import parse_bugs, parse_test_case_summaries
from qa_intelligence.mcp.runtime import get_container
from qa_intelligence.prompts.analysis_guidance import generation_guidance


async def generate_coverage_report(
    user_story_id: int,
    requirement_analysis: dict[str, Any] | None = None,
    existing_test_cases: list[dict[str, Any]] | None = None,
    similar_test_cases: list[dict[str, Any]] | None = None,
    related_bugs: list[dict[str, Any]] | None = None,
    drafts: list[dict[str, Any]] | None = None,
) -> dict[str, object]:
    """Generate a coverage report with covered, duplicate, bug-covered, and missing scenarios."""
    try:
        container = get_container()
        story = await container.story_service.get_user_story(user_story_id)

        existing = parse_test_case_summaries(existing_test_cases, id_base=720_000)
        similar = parse_test_case_summaries(similar_test_cases, id_base=730_000)
        bugs = parse_bugs(related_bugs)
        draft_summaries = parse_test_case_summaries(drafts, id_base=740_000)

        # Prefer caller inventory; otherwise fetch linked cases / bugs from ADO.
        if existing_test_cases is None:
            existing = await container.test_case_service.list_existing(user_story_id)
        if related_bugs is None:
            bugs = await container.bug_service.list_related(user_story_id)

        inventory = [*existing, *similar, *draft_summaries]

        if requirement_analysis is not None:
            analysis = RequirementAnalysis.model_validate(requirement_analysis)
        else:
            analysis = container.requirement_analysis_service.analyze_story(story)

        coverage = container.coverage_analysis_service.analyze(story, inventory, bugs)
        duplicates = container.duplicate_detection_service.detect(story, inventory, bugs)
        strategy = container.test_strategy_service.build_strategy(
            analysis,
            coverage,
            duplicates,
        )

        covered: list[ScenarioRef] = []
        bug_covered: list[ScenarioRef] = []
        for row in coverage.matrix:
            if row.status == CoverageStatus.COVERED_BY_TEST:
                covered.append(
                    ScenarioRef(
                        key=row.ac_id,
                        title=row.ac_text,
                        source=ScenarioSource.EXISTING,
                        related_ids=list(row.matched_test_case_ids),
                    )
                )
            elif row.status == CoverageStatus.COVERED_BY_BUG:
                bug_covered.append(
                    ScenarioRef(
                        key=row.ac_id,
                        title=row.ac_text,
                        source=ScenarioSource.BUG,
                        related_ids=list(row.matched_bug_ids),
                    )
                )

        missing = list(coverage.uncovered_scenarios)
        duplicate_refs = [
            ScenarioRef(
                key=match.key,
                title=match.title,
                source=ScenarioSource.EXISTING,
                related_ids=list(match.matched_test_case_ids),
            )
            for match in duplicates.duplicate
        ]

        qa_final = strategy.qa_strategy.model_copy(
            update={
                "blocked": strategy.blocked,
                "estimates": CoverageEstimates(
                    estimated_new_test_cases=len(missing),
                    estimated_existing_coverage=len(covered) + len(bug_covered),
                    estimated_duplicate_scenarios=len(duplicate_refs),
                    preliminary=False,
                ),
            }
        )
        directive = strategy.generation_directive
        if qa_final.blocked:
            directive = GenerationDirective.BLOCKED
        elif not inventory and missing:
            directive = GenerationDirective.FRESH_SUITE
        elif inventory:
            directive = GenerationDirective.GAP_FILL_ONLY

        report = CoverageReport(
            user_story_id=user_story_id,
            covered_scenarios=covered,
            duplicate_scenarios=duplicate_refs,
            bug_covered_scenarios=bug_covered,
            missing_scenarios=missing,
            qa_strategy_final=qa_final,
            generation_directive=directive,
        )

        return responses.success(
            report,
            warnings=[generation_guidance()],
        ).model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        return responses.from_exception(exc, tool_name="generate_coverage_report").model_dump(
            mode="json"
        )
