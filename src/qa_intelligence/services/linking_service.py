"""LinkingService — link test cases to user stories."""

from __future__ import annotations

import structlog

from qa_intelligence.domain.enums import LinkStatus
from qa_intelligence.domain.models.write_results import LinkResult
from qa_intelligence.infrastructure.errors import QaIntelligenceError, WriteError
from qa_intelligence.repositories.protocols import TestCaseRepository

logger = structlog.get_logger(__name__)


class LinkingService:
    """Create ADO relations between test cases and a user story."""

    def __init__(self, test_case_repository: TestCaseRepository) -> None:
        self._test_case_repository = test_case_repository

    async def link(
        self,
        user_story_id: int,
        test_case_ids: list[int],
        *,
        dry_run: bool = False,
    ) -> list[LinkResult]:
        results: list[LinkResult] = []
        for test_case_id in test_case_ids:
            if dry_run:
                results.append(
                    LinkResult(
                        test_case_id=test_case_id,
                        status=LinkStatus.SKIPPED,
                        message="dry_run: link not applied",
                    )
                )
                continue
            try:
                await self._test_case_repository.link_to_user_story(
                    user_story_id,
                    test_case_id,
                )
            except WriteError as exc:
                results.append(
                    LinkResult(
                        test_case_id=test_case_id,
                        status=LinkStatus.FAILED,
                        message=exc.message,
                    )
                )
                logger.warning(
                    "link.failed",
                    user_story_id=user_story_id,
                    test_case_id=test_case_id,
                    error=exc.message,
                )
                continue
            except QaIntelligenceError as exc:
                results.append(
                    LinkResult(
                        test_case_id=test_case_id,
                        status=LinkStatus.FAILED,
                        message=exc.message,
                    )
                )
                continue

            results.append(
                LinkResult(
                    test_case_id=test_case_id,
                    status=LinkStatus.LINKED,
                    message="Linked to user story",
                )
            )
            logger.info(
                "link.succeeded",
                user_story_id=user_story_id,
                test_case_id=test_case_id,
            )
        return results
