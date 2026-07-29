"""TestCaseService — inventory, validate, and publish test cases.

Enforces product Rules 1, 7, 8, 9, and requirement-block (Rule 10 upstream).
"""

from __future__ import annotations

import structlog

from qa_intelligence.domain.enums import CreateStatus
from qa_intelligence.domain.models.read_models import TestCaseSummary
from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.domain.models.validation import ValidationResult
from qa_intelligence.domain.models.write_results import CreateResult
from qa_intelligence.domain.validation.duplicate_guard import (
    find_intra_batch_duplicates,
    is_duplicate_of_existing,
)
from qa_intelligence.domain.validation.test_case_validator import validate_test_case_payload
from qa_intelligence.infrastructure.errors import QaIntelligenceError, WriteError
from qa_intelligence.repositories.protocols import TestCaseRepository

logger = structlog.get_logger(__name__)


class TestCaseService:
    """Inventory existing cases; validate and optionally create drafts in ADO."""

    __test__ = False

    def __init__(self, test_case_repository: TestCaseRepository) -> None:
        self._test_case_repository = test_case_repository

    async def list_existing(self, user_story_id: int) -> list[TestCaseSummary]:
        cases = await self._test_case_repository.list_linked_to_story(user_story_id)
        logger.info(
            "test_cases.existing_fetched",
            user_story_id=user_story_id,
            count=len(cases),
        )
        return cases

    def validate_many(
        self,
        drafts: list[TestCase] | list[dict[str, object]],
        *,
        existing_test_cases: list[TestCaseSummary] | None = None,
        reject_duplicates: bool = True,
    ) -> tuple[list[TestCase], list[CreateResult]]:
        """Validate drafts; return valid cases and per-item CreateResults (no ADO)."""
        validated: list[TestCase] = []
        results: list[CreateResult] = []
        existing = existing_test_cases or []

        coerced: list[tuple[int, TestCase | None, ValidationResult, str | None]] = []
        for index, draft in enumerate(drafts):
            case, validation = self._coerce_and_validate(draft)
            coerced.append((index, case, validation, _draft_title(draft)))

        valid_cases = [case for _, case, validation, _ in coerced if case and validation.is_valid]
        intra: dict[int, int] = {}
        if reject_duplicates and valid_cases:
            # Map among validated-only indices in coerced order.
            valid_indices = [
                index for index, case, validation, _ in coerced if case and validation.is_valid
            ]
            index_map = find_intra_batch_duplicates(valid_cases)
            for later_pos, earlier_pos in index_map.items():
                intra[valid_indices[later_pos]] = valid_indices[earlier_pos]

        for index, case, validation, title in coerced:
            if case is None or not validation.is_valid:
                results.append(
                    CreateResult(
                        index=index,
                        status=CreateStatus.REJECTED,
                        title=title,
                        validation_errors=[e.message for e in validation.errors],
                        warnings=[w.message for w in validation.warnings],
                        message="Rejected by validation",
                    )
                )
                continue

            if reject_duplicates and index in intra:
                results.append(
                    CreateResult(
                        index=index,
                        status=CreateStatus.REJECTED,
                        title=case.title,
                        validation_errors=[
                            f"Duplicate of batch item at index {intra[index]}"
                        ],
                        message="Rejected as duplicate (Rule 1)",
                    )
                )
                continue

            if reject_duplicates:
                is_dup, score, matched = is_duplicate_of_existing(case, existing)
                if is_dup:
                    results.append(
                        CreateResult(
                            index=index,
                            status=CreateStatus.REJECTED,
                            title=case.title,
                            validation_errors=[
                                f"Duplicate of existing case '{matched}' "
                                f"(similarity={score:.2f})"
                            ],
                            message="Rejected as duplicate (Rule 1)",
                        )
                    )
                    continue

            validated.append(case)
            results.append(
                CreateResult(
                    index=index,
                    status=CreateStatus.VALIDATED_ONLY,
                    title=case.title,
                    warnings=[w.message for w in validation.warnings],
                    message="Validated",
                )
            )
        return validated, results

    async def create_many(
        self,
        drafts: list[TestCase] | list[dict[str, object]],
        *,
        dry_run: bool = False,
        requirement_blocked: bool = False,
        override_requirement_block: bool = False,
        reject_duplicates: bool = True,
        existing_test_cases: list[TestCaseSummary] | None = None,
    ) -> list[CreateResult]:
        """Validate then optionally publish each draft. Per-item results."""
        if requirement_blocked and not override_requirement_block:
            return [
                CreateResult(
                    index=index,
                    status=CreateStatus.REJECTED,
                    title=_draft_title(draft),
                    validation_errors=["REQUIREMENT_BLOCKED"],
                    message="Requirement gaps forbid creating test cases",
                )
                for index, draft in enumerate(drafts)
            ]

        validated, validation_results = self.validate_many(
            drafts,
            existing_test_cases=existing_test_cases,
            reject_duplicates=reject_duplicates,
        )
        if dry_run:
            return validation_results

        results: list[CreateResult] = []
        validated_iter = iter(validated)
        for result in validation_results:
            if result.status == CreateStatus.REJECTED:
                results.append(result)
                continue

            case = next(validated_iter)
            try:
                created_id = await self._test_case_repository.create(case)
            except WriteError as exc:
                results.append(
                    CreateResult(
                        index=result.index,
                        status=CreateStatus.REJECTED,
                        title=case.title,
                        validation_errors=[exc.message],
                        message="ADO create failed",
                    )
                )
                logger.warning(
                    "test_cases.create_failed",
                    index=result.index,
                    error=exc.message,
                )
                continue
            except QaIntelligenceError as exc:
                results.append(
                    CreateResult(
                        index=result.index,
                        status=CreateStatus.REJECTED,
                        title=case.title,
                        validation_errors=[exc.message],
                        message=exc.code,
                    )
                )
                continue

            results.append(
                CreateResult(
                    index=result.index,
                    status=CreateStatus.CREATED,
                    id=created_id,
                    title=case.title,
                    message="Created in Azure DevOps",
                )
            )
            logger.info(
                "test_cases.created",
                index=result.index,
                test_case_id=created_id,
            )

        return results

    def _coerce_and_validate(
        self,
        draft: TestCase | dict[str, object],
    ) -> tuple[TestCase | None, ValidationResult]:
        if isinstance(draft, TestCase):
            payload = draft.model_dump()
        else:
            payload = draft
        return validate_test_case_payload(payload)


def _draft_title(draft: TestCase | dict[str, object]) -> str | None:
    if isinstance(draft, TestCase):
        return draft.title
    title = draft.get("title")
    return str(title) if title else None
