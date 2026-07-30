"""OrchestrationService — end-to-end QA workflow.

Workflow:
  Fetch User Story → Analyze Requirement → Fetch Existing Test Cases →
  Fetch Bugs → Duplicate Detection → Coverage Analysis → Test Strategy →
  Generate Test Cases → Validate Test Cases → Publish to Azure DevOps →
  Link Test Cases → return complete execution summary.
"""

from __future__ import annotations

import structlog

from qa_intelligence.domain.enums import CreateStatus, GenerationDirective, LinkStatus
from qa_intelligence.domain.models.orchestration import (
    WorkflowExecutionSummary,
    WorkflowStepName,
    WorkflowStepResult,
    WorkflowStepStatus,
)
from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.infrastructure.errors import ConfigurationError, QaIntelligenceError
from qa_intelligence.services.bug_service import BugService
from qa_intelligence.services.code_intelligence_service import CodeIntelligenceService
from qa_intelligence.services.coverage_analysis_service import CoverageAnalysisService
from qa_intelligence.services.duplicate_detection_service import DuplicateDetectionService
from qa_intelligence.services.linking_service import LinkingService
from qa_intelligence.services.requirement_analysis_service import RequirementAnalysisService
from qa_intelligence.services.story_service import StoryService
from qa_intelligence.services.test_case_generation_service import TestCaseGenerationService
from qa_intelligence.services.test_case_service import TestCaseService
from qa_intelligence.services.test_strategy_service import TestStrategyService

logger = structlog.get_logger(__name__)


class OrchestrationService:
    """Run the complete QA Intelligence workflow and return an execution summary."""

    def __init__(
        self,
        *,
        story_service: StoryService,
        requirement_analysis_service: RequirementAnalysisService,
        test_case_service: TestCaseService,
        bug_service: BugService,
        duplicate_detection_service: DuplicateDetectionService,
        coverage_analysis_service: CoverageAnalysisService,
        test_strategy_service: TestStrategyService,
        test_case_generation_service: TestCaseGenerationService,
        linking_service: LinkingService,
        code_intelligence_service: CodeIntelligenceService | None = None,
    ) -> None:
        self._story_service = story_service
        self._requirement_analysis_service = requirement_analysis_service
        self._test_case_service = test_case_service
        self._bug_service = bug_service
        self._duplicate_detection_service = duplicate_detection_service
        self._coverage_analysis_service = coverage_analysis_service
        self._test_strategy_service = test_strategy_service
        self._test_case_generation_service = test_case_generation_service
        self._linking_service = linking_service
        self._code_intelligence_service = code_intelligence_service or CodeIntelligenceService()

    async def run(
        self,
        user_story_id: int,
        *,
        dry_run: bool = True,
        override_requirement_block: bool = False,
        publish: bool = False,
        link: bool = True,
        repository_path: str | None = None,
        ado_repository: str | None = None,
        ado_branch: str | None = None,
        ado_project: str | None = None,
        ado_writes_enabled: bool | None = None,
    ) -> WorkflowExecutionSummary:
        """Execute the full workflow for a user story and return a summary.

        Defaults: dry_run=true, publish=false — no ADO work-item writes.
        Real publish requires publish=true, dry_run=false, and
        ADO_WRITES_ENABLED=true (or ado_writes_enabled=True override for tests).

        Code Intelligence runs when ``repository_path`` and/or ``ado_repository``
        (or ``ADO_DEFAULT_GIT_REPOSITORY``) is available. Azure Repos access is
        read-only (clone/fetch only; never push).
        """
        from qa_intelligence.infrastructure.config import get_settings

        writes_ok = (
            ado_writes_enabled
            if ado_writes_enabled is not None
            else get_settings().ado_writes_enabled
        )
        if publish and not dry_run and not writes_ok:
            raise ConfigurationError(
                "Refusing to publish to Azure DevOps: ADO_WRITES_ENABLED is false. "
                "Run with dry_run=true / publish=false to draft only.",
                details={"publish": publish, "dry_run": dry_run},
            )

        summary = WorkflowExecutionSummary(
            user_story_id=user_story_id,
            ok=False,
            dry_run=dry_run,
        )

        # 1. Fetch User Story
        try:
            story = await self._story_service.get_user_story(user_story_id)
        except QaIntelligenceError as exc:
            summary.steps.append(
                _step(
                    WorkflowStepName.FETCH_USER_STORY,
                    WorkflowStepStatus.FAILED,
                    exc.message,
                    {"code": exc.code},
                )
            )
            summary.notes = f"Stopped: failed to fetch user story ({exc.code})."
            return summary

        summary.user_story = story
        summary.steps.append(
            _step(
                WorkflowStepName.FETCH_USER_STORY,
                WorkflowStepStatus.SUCCEEDED,
                f"Fetched user story '{story.title}'",
                {"acceptance_criteria": len(story.acceptance_criteria)},
            )
        )

        # 2. Analyze Requirement
        try:
            analysis = self._requirement_analysis_service.analyze_story(story)
        except QaIntelligenceError as exc:
            summary.steps.append(
                _step(
                    WorkflowStepName.ANALYZE_REQUIREMENT,
                    WorkflowStepStatus.FAILED,
                    exc.message,
                    {"code": exc.code},
                )
            )
            summary.notes = "Stopped: requirement analysis failed."
            return summary

        summary.requirement_analysis = analysis
        summary.blocked = analysis.blocked
        summary.steps.append(
            _step(
                WorkflowStepName.ANALYZE_REQUIREMENT,
                WorkflowStepStatus.BLOCKED if analysis.blocked else WorkflowStepStatus.SUCCEEDED,
                (
                    "Requirement blocked by gaps"
                    if analysis.blocked
                    else "Requirement analysis completed"
                ),
                {
                    "feature_type": analysis.qa_strategy.feature_type.value,
                    "risk": analysis.qa_strategy.risk.value,
                    "gap_count": len(analysis.requirement_gaps),
                    "blocked": analysis.blocked,
                },
            )
        )

        if analysis.blocked and not override_requirement_block:
            summary.generation_directive = GenerationDirective.BLOCKED
            summary.notes = (
                "Workflow stopped: requirement gaps block generation. "
                "Pass override_requirement_block=true to continue."
            )
            self._mark_remaining_skipped(
                summary,
                from_step=WorkflowStepName.CODE_INTELLIGENCE,
                reason="Blocked by incomplete requirements",
            )
            return summary

        # 2b. Code Intelligence (optional — skipped when no local/ADO source)
        implementation_summary = None
        has_code_source = bool(
            (repository_path and repository_path.strip())
            or (ado_repository and ado_repository.strip())
            or self._code_intelligence_service.has_default_ado_repository
        )
        if has_code_source:
            try:
                implementation_summary = self._code_intelligence_service.analyze(
                    story,
                    repository_path,
                    ado_repository=ado_repository,
                    ado_branch=ado_branch,
                    ado_project=ado_project,
                )
                summary.implementation_summary = implementation_summary
                summary.steps.append(
                    _step(
                        WorkflowStepName.CODE_INTELLIGENCE,
                        WorkflowStepStatus.SUCCEEDED,
                        f"Code intelligence analyzed {implementation_summary.files_read} file(s)",
                        {
                            "files_read": implementation_summary.files_read,
                            "affected_files": len(implementation_summary.affected_files),
                            "validation_rules": len(implementation_summary.validation_rules),
                            "source_kind": implementation_summary.source_kind.value,
                            "ado_repository": implementation_summary.ado_repository,
                            "ado_branch": implementation_summary.ado_branch,
                            "ado_commit": implementation_summary.ado_commit,
                        },
                    )
                )
            except QaIntelligenceError as exc:
                summary.steps.append(
                    _step(
                        WorkflowStepName.CODE_INTELLIGENCE,
                        WorkflowStepStatus.FAILED,
                        exc.message,
                        {"code": exc.code},
                    )
                )
                # Non-fatal: continue without implementation enrichment.
                summary.notes = (
                    "Code intelligence failed; continuing with requirement-only generation. "
                    f"({exc.code})"
                )
        else:
            summary.steps.append(
                _step(
                    WorkflowStepName.CODE_INTELLIGENCE,
                    WorkflowStepStatus.SKIPPED,
                    "No repository_path or ado_repository provided",
                )
            )

        # 3. Fetch Existing Test Cases
        try:
            existing = await self._test_case_service.list_existing(user_story_id)
        except QaIntelligenceError as exc:
            summary.steps.append(
                _step(
                    WorkflowStepName.FETCH_EXISTING_TEST_CASES,
                    WorkflowStepStatus.FAILED,
                    exc.message,
                    {"code": exc.code},
                )
            )
            summary.notes = "Stopped: failed to fetch existing test cases."
            return summary

        summary.existing_test_cases = existing
        summary.steps.append(
            _step(
                WorkflowStepName.FETCH_EXISTING_TEST_CASES,
                WorkflowStepStatus.SUCCEEDED,
                f"Fetched {len(existing)} existing test case(s)",
                {"count": len(existing)},
            )
        )

        # 4. Fetch Bugs
        try:
            bugs = await self._bug_service.list_related(user_story_id)
        except QaIntelligenceError as exc:
            summary.steps.append(
                _step(
                    WorkflowStepName.FETCH_BUGS,
                    WorkflowStepStatus.FAILED,
                    exc.message,
                    {"code": exc.code},
                )
            )
            summary.notes = "Stopped: failed to fetch related bugs."
            return summary

        summary.related_bugs = bugs
        summary.steps.append(
            _step(
                WorkflowStepName.FETCH_BUGS,
                WorkflowStepStatus.SUCCEEDED,
                f"Fetched {len(bugs)} related bug(s)",
                {"count": len(bugs)},
            )
        )

        # 5. Duplicate Detection
        try:
            duplicates = self._duplicate_detection_service.detect(
                story,
                existing,
                bugs,
            )
        except QaIntelligenceError as exc:
            summary.steps.append(
                _step(
                    WorkflowStepName.DUPLICATE_DETECTION,
                    WorkflowStepStatus.FAILED,
                    exc.message,
                    {"code": exc.code},
                )
            )
            summary.notes = "Stopped: duplicate detection failed."
            return summary

        summary.duplicate_detection = duplicates
        summary.steps.append(
            _step(
                WorkflowStepName.DUPLICATE_DETECTION,
                WorkflowStepStatus.SUCCEEDED,
                "Duplicate detection completed",
                {
                    "duplicate_count": len(duplicates.duplicate),
                    "generate_new_count": len(duplicates.generate_new),
                },
            )
        )

        # 6. Coverage Analysis
        try:
            coverage = self._coverage_analysis_service.analyze(
                story,
                existing,
                bugs,
            )
        except QaIntelligenceError as exc:
            summary.steps.append(
                _step(
                    WorkflowStepName.COVERAGE_ANALYSIS,
                    WorkflowStepStatus.FAILED,
                    exc.message,
                    {"code": exc.code},
                )
            )
            summary.notes = "Stopped: coverage analysis failed."
            return summary

        summary.coverage_analysis = coverage
        summary.steps.append(
            _step(
                WorkflowStepName.COVERAGE_ANALYSIS,
                WorkflowStepStatus.SUCCEEDED,
                f"Coverage analysis found {len(coverage.uncovered_scenarios)} uncovered scenario(s)",
                {
                    "uncovered": len(coverage.uncovered_scenarios),
                    "covered_by_test": coverage.covered_by_test_count,
                    "covered_by_bug": coverage.covered_by_bug_count,
                },
            )
        )

        # 7. Test Strategy
        try:
            strategy = self._test_strategy_service.build_strategy(
                analysis,
                coverage,
                duplicates,
            )
        except QaIntelligenceError as exc:
            summary.steps.append(
                _step(
                    WorkflowStepName.TEST_STRATEGY,
                    WorkflowStepStatus.FAILED,
                    exc.message,
                    {"code": exc.code},
                )
            )
            summary.notes = "Stopped: test strategy failed."
            return summary

        summary.test_strategy = strategy
        summary.generation_directive = strategy.generation_directive
        summary.blocked = strategy.blocked or summary.blocked
        summary.steps.append(
            _step(
                WorkflowStepName.TEST_STRATEGY,
                WorkflowStepStatus.BLOCKED if strategy.blocked else WorkflowStepStatus.SUCCEEDED,
                f"Strategy directive={strategy.generation_directive.value}",
                {
                    "estimated_new_test_cases": strategy.estimated_new_test_cases,
                    "directive": strategy.generation_directive.value,
                },
            )
        )

        if strategy.blocked and not override_requirement_block:
            summary.notes = "Workflow stopped: strategy blocked generation."
            self._mark_remaining_skipped(
                summary,
                from_step=WorkflowStepName.GENERATE_TEST_CASES,
                reason="Blocked by strategy",
            )
            return summary

        # 8. Generate Test Cases
        try:
            generation = self._test_case_generation_service.generate(
                strategy,
                story,
                list(story.acceptance_criteria),
                existing_test_cases=existing,
                uncovered_scenarios=list(coverage.uncovered_scenarios),
                implementation_summary=summary.implementation_summary,
            )
        except QaIntelligenceError as exc:
            summary.steps.append(
                _step(
                    WorkflowStepName.GENERATE_TEST_CASES,
                    WorkflowStepStatus.FAILED,
                    exc.message,
                    {"code": exc.code},
                )
            )
            summary.notes = "Stopped: test case generation failed."
            return summary

        summary.generation = generation
        summary.steps.append(
            _step(
                WorkflowStepName.GENERATE_TEST_CASES,
                WorkflowStepStatus.SUCCEEDED,
                f"Generated {len(generation.generated)} draft test case(s)",
                {
                    "mode": generation.mode.value,
                    "generated": len(generation.generated),
                    "rejected_during_generation": generation.rejected_count,
                },
            )
        )

        drafts: list[TestCase] = list(generation.generated)
        if not drafts:
            summary.steps.append(
                _step(
                    WorkflowStepName.VALIDATE_TEST_CASES,
                    WorkflowStepStatus.SKIPPED,
                    "No drafts to validate",
                )
            )
            summary.steps.append(
                _step(
                    WorkflowStepName.PUBLISH_TO_AZURE_DEVOPS,
                    WorkflowStepStatus.SKIPPED,
                    "No drafts to publish",
                )
            )
            summary.steps.append(
                _step(
                    WorkflowStepName.LINK_TEST_CASES,
                    WorkflowStepStatus.SKIPPED,
                    "No test cases to link",
                )
            )
            summary.ok = True
            summary.notes = "Workflow completed with no new test cases to create."
            return summary

        # 9. Validate Test Cases (Rules 1, 7–9)
        validated, validation_results = self._test_case_service.validate_many(
            drafts,
            existing_test_cases=existing,
            reject_duplicates=True,
        )
        summary.validated_test_cases = validated
        rejected = sum(1 for r in validation_results if r.status == CreateStatus.REJECTED)
        summary.rejected_count = rejected
        summary.steps.append(
            _step(
                WorkflowStepName.VALIDATE_TEST_CASES,
                WorkflowStepStatus.SUCCEEDED if validated else WorkflowStepStatus.FAILED,
                f"Validated {len(validated)} case(s); rejected {rejected}",
                {"validated": len(validated), "rejected": rejected},
            )
        )

        if not validated:
            summary.create_results = validation_results
            summary.steps.append(
                _step(
                    WorkflowStepName.PUBLISH_TO_AZURE_DEVOPS,
                    WorkflowStepStatus.SKIPPED,
                    "All drafts rejected by validation",
                )
            )
            summary.steps.append(
                _step(
                    WorkflowStepName.LINK_TEST_CASES,
                    WorkflowStepStatus.SKIPPED,
                    "Nothing to link",
                )
            )
            summary.ok = False
            summary.notes = "Workflow stopped: all generated drafts failed validation."
            return summary

        # 10. Publish to Azure DevOps
        if not publish:
            summary.create_results = [
                r.model_copy(update={"status": CreateStatus.VALIDATED_ONLY})
                for r in validation_results
                if r.status != CreateStatus.REJECTED
            ] + [r for r in validation_results if r.status == CreateStatus.REJECTED]
            summary.steps.append(
                _step(
                    WorkflowStepName.PUBLISH_TO_AZURE_DEVOPS,
                    WorkflowStepStatus.SKIPPED,
                    "Publish disabled by caller",
                )
            )
            summary.steps.append(
                _step(
                    WorkflowStepName.LINK_TEST_CASES,
                    WorkflowStepStatus.SKIPPED,
                    "Link skipped because publish was disabled",
                )
            )
            summary.ok = True
            summary.notes = "Workflow completed through validation (publish disabled)."
            return summary

        try:
            create_results = await self._test_case_service.create_many(
                validated,
                dry_run=dry_run,
                requirement_blocked=analysis.blocked or strategy.blocked,
                override_requirement_block=override_requirement_block,
                reject_duplicates=True,
                existing_test_cases=existing,
            )
        except QaIntelligenceError as exc:
            summary.steps.append(
                _step(
                    WorkflowStepName.PUBLISH_TO_AZURE_DEVOPS,
                    WorkflowStepStatus.FAILED,
                    exc.message,
                    {"code": exc.code},
                )
            )
            summary.notes = "Stopped: publish to Azure DevOps failed."
            return summary

        summary.create_results = create_results
        created_ids = [
            r.id for r in create_results if r.status == CreateStatus.CREATED and r.id is not None
        ]
        validated_only_ids_count = sum(
            1 for r in create_results if r.status == CreateStatus.VALIDATED_ONLY
        )
        publish_rejected = sum(1 for r in create_results if r.status == CreateStatus.REJECTED)
        summary.created_ids = created_ids
        summary.rejected_count += publish_rejected

        if dry_run:
            summary.steps.append(
                _step(
                    WorkflowStepName.PUBLISH_TO_AZURE_DEVOPS,
                    WorkflowStepStatus.SUCCEEDED,
                    f"dry_run: validated {validated_only_ids_count} case(s); no ADO writes",
                    {"validated_only": validated_only_ids_count, "rejected": publish_rejected},
                )
            )
        else:
            summary.steps.append(
                _step(
                    WorkflowStepName.PUBLISH_TO_AZURE_DEVOPS,
                    WorkflowStepStatus.SUCCEEDED if created_ids or not validated else WorkflowStepStatus.FAILED,
                    f"Published {len(created_ids)} test case(s) to Azure DevOps",
                    {"created": len(created_ids), "rejected": publish_rejected},
                )
            )

        # 11. Link Test Cases
        ids_to_link = created_ids
        if dry_run:
            # dry_run create yields no ids — link step reports dry-run skip for validated count
            summary.link_results = await self._linking_service.link(
                user_story_id,
                [],
                dry_run=True,
            )
            summary.steps.append(
                _step(
                    WorkflowStepName.LINK_TEST_CASES,
                    WorkflowStepStatus.SKIPPED if not ids_to_link else WorkflowStepStatus.SUCCEEDED,
                    f"dry_run: link not applied ({len(validated)} validated case(s))",
                    {"would_link": len(validated)},
                )
            )
            summary.ok = True
            summary.notes = (
                f"Dry-run completed: {len(validated)} validated draft(s); "
                "no Azure DevOps writes."
            )
            logger.info(
                "orchestration.completed",
                user_story_id=user_story_id,
                dry_run=True,
                validated=len(validated),
            )
            return summary

        if not link:
            summary.steps.append(
                _step(
                    WorkflowStepName.LINK_TEST_CASES,
                    WorkflowStepStatus.SKIPPED,
                    "Link disabled by caller",
                    {"unlinked_created_ids": created_ids},
                )
            )
            summary.ok = True
            summary.notes = (
                f"Published {len(created_ids)} case(s); linking skipped by caller."
            )
            return summary

        if not ids_to_link:
            summary.steps.append(
                _step(
                    WorkflowStepName.LINK_TEST_CASES,
                    WorkflowStepStatus.SKIPPED,
                    "No created test case ids to link",
                )
            )
            summary.ok = publish_rejected == 0
            summary.notes = "No test cases were created to link."
            return summary

        try:
            link_results = await self._linking_service.link(user_story_id, ids_to_link)
        except QaIntelligenceError as exc:
            summary.steps.append(
                _step(
                    WorkflowStepName.LINK_TEST_CASES,
                    WorkflowStepStatus.FAILED,
                    exc.message,
                    {"code": exc.code},
                )
            )
            summary.ok = False
            summary.notes = (
                f"Created {len(created_ids)} case(s) but linking failed: {exc.message}"
            )
            return summary

        summary.link_results = link_results
        linked_ids = [r.test_case_id for r in link_results if r.status == LinkStatus.LINKED]
        failed_links = [r for r in link_results if r.status == LinkStatus.FAILED]
        summary.linked_ids = linked_ids
        summary.steps.append(
            _step(
                WorkflowStepName.LINK_TEST_CASES,
                WorkflowStepStatus.SUCCEEDED if not failed_links else WorkflowStepStatus.FAILED,
                f"Linked {len(linked_ids)} / {len(ids_to_link)} test case(s)",
                {"linked": len(linked_ids), "failed": len(failed_links)},
            )
        )

        summary.ok = len(failed_links) == 0 and len(created_ids) > 0
        summary.notes = (
            f"Workflow completed: created {len(created_ids)}, "
            f"linked {len(linked_ids)}, rejected {summary.rejected_count}."
        )
        logger.info(
            "orchestration.completed",
            user_story_id=user_story_id,
            created=len(created_ids),
            linked=len(linked_ids),
            rejected=summary.rejected_count,
            ok=summary.ok,
        )
        return summary

    def _mark_remaining_skipped(
        self,
        summary: WorkflowExecutionSummary,
        *,
        from_step: WorkflowStepName,
        reason: str,
    ) -> None:
        started = False
        for name in WorkflowStepName:
            if name == from_step:
                started = True
            if not started:
                continue
            # Avoid duplicating steps already recorded.
            if any(step.name == name for step in summary.steps):
                continue
            summary.steps.append(
                _step(name, WorkflowStepStatus.SKIPPED, reason)
            )


def _step(
    name: WorkflowStepName,
    status: WorkflowStepStatus,
    message: str = "",
    details: dict[str, object] | None = None,
) -> WorkflowStepResult:
    return WorkflowStepResult(
        name=name,
        status=status,
        message=message,
        details=details or {},
    )
