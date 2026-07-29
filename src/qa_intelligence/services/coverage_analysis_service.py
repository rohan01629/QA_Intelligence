"""CoverageAnalysisService — AC/test/bug mapping and uncovered-scenario output.

Builds a coverage matrix and returns only uncovered requirement scenarios
as the primary generation input. Does NOT generate test cases.
"""

from __future__ import annotations

import structlog

from qa_intelligence.domain.enums import ScenarioSource
from qa_intelligence.domain.models.bug import Bug
from qa_intelligence.domain.models.coverage import ScenarioRef
from qa_intelligence.domain.models.coverage_matrix import (
    AcceptanceCriterionMap,
    BugMapEntry,
    CoverageAnalysisResult,
    CoverageMatrixRow,
    CoverageStatus,
    TestCaseMapEntry,
)
from qa_intelligence.domain.models.read_models import TestCaseSummary
from qa_intelligence.domain.models.user_story import UserStory
from qa_intelligence.domain.similarity import (
    FeatureSimilarityScorer,
    ScenarioText,
    SimilarityScorer,
)

logger = structlog.get_logger(__name__)


class CoverageAnalysisService:
    """Map requirements to inventory and identify uncovered scenarios only."""

    def __init__(
        self,
        *,
        scorer: SimilarityScorer | None = None,
        covered_threshold: float = 0.72,
        partial_threshold: float = 0.50,
    ) -> None:
        self._scorer = scorer or FeatureSimilarityScorer()
        self._covered_threshold = covered_threshold
        self._partial_threshold = partial_threshold

    def analyze(
        self,
        user_story: UserStory,
        existing_test_cases: list[TestCaseSummary],
        related_bugs: list[Bug] | None = None,
    ) -> CoverageAnalysisResult:
        """Build coverage mappings/matrix and return uncovered scenarios."""
        related_bugs = related_bugs or []

        acceptance_criteria = self.map_acceptance_criteria(user_story)
        test_cases = self.map_test_cases(existing_test_cases)
        bugs = self.map_bugs(related_bugs)
        matrix = self.build_coverage_matrix(
            user_story,
            existing_test_cases,
            related_bugs,
        )
        uncovered = self.identify_uncovered_scenarios(matrix)

        covered_by_test = sum(
            1 for row in matrix if row.status == CoverageStatus.COVERED_BY_TEST
        )
        covered_by_bug = sum(
            1 for row in matrix if row.status == CoverageStatus.COVERED_BY_BUG
        )
        partial = sum(1 for row in matrix if row.status == CoverageStatus.PARTIAL)
        uncovered_count = sum(
            1 for row in matrix if row.status == CoverageStatus.UNCOVERED
        )

        result = CoverageAnalysisResult(
            user_story_id=user_story.id,
            acceptance_criteria=acceptance_criteria,
            test_cases=test_cases,
            bugs=bugs,
            matrix=matrix,
            uncovered_scenarios=uncovered,
            covered_by_test_count=covered_by_test,
            covered_by_bug_count=covered_by_bug,
            partial_count=partial,
            uncovered_count=uncovered_count,
        )

        logger.info(
            "coverage.analysis_completed",
            user_story_id=user_story.id,
            ac_count=len(acceptance_criteria),
            test_case_count=len(test_cases),
            bug_count=len(bugs),
            uncovered=len(uncovered),
            covered_by_test=covered_by_test,
            covered_by_bug=covered_by_bug,
            partial=partial,
        )
        return result

    def uncovered_scenarios(
        self,
        user_story: UserStory,
        existing_test_cases: list[TestCaseSummary],
        related_bugs: list[Bug] | None = None,
    ) -> list[ScenarioRef]:
        """Convenience API: return only uncovered scenarios."""
        return self.analyze(user_story, existing_test_cases, related_bugs).uncovered_scenarios

    def map_acceptance_criteria(self, user_story: UserStory) -> list[AcceptanceCriterionMap]:
        return [
            AcceptanceCriterionMap(
                ac_id=ac.id or f"AC-{ac.order}",
                order=ac.order,
                text=ac.text,
            )
            for ac in user_story.acceptance_criteria
        ]

    def map_test_cases(
        self,
        existing_test_cases: list[TestCaseSummary],
    ) -> list[TestCaseMapEntry]:
        return [
            TestCaseMapEntry(
                test_case_id=tc.id,
                title=tc.title,
                steps=list(tc.steps),
                expected_results=list(tc.expected_results),
                state=tc.state,
            )
            for tc in existing_test_cases
        ]

    def map_bugs(self, related_bugs: list[Bug]) -> list[BugMapEntry]:
        return [
            BugMapEntry(
                bug_id=bug.id,
                title=bug.title,
                state=bug.state,
                severity=bug.severity,
                repro_steps=bug.repro_steps,
            )
            for bug in related_bugs
        ]

    def build_coverage_matrix(
        self,
        user_story: UserStory,
        existing_test_cases: list[TestCaseSummary],
        related_bugs: list[Bug],
    ) -> list[CoverageMatrixRow]:
        """Generate AC × inventory coverage matrix using semantic similarity."""
        ac_texts = [ac.text for ac in user_story.acceptance_criteria]
        test_scenarios = [
            ScenarioText.from_parts(
                title=tc.title,
                steps=tc.steps,
                expected_results=tc.expected_results,
                ac_texts=ac_texts,
                source_id=tc.id,
                key=f"tc:{tc.id}",
            )
            for tc in existing_test_cases
        ]
        bug_scenarios = [
            ScenarioText.from_parts(
                title=bug.title,
                steps=_split_lines(bug.repro_steps),
                expected_results=[],
                ac_texts=ac_texts,
                source_id=bug.id,
                key=f"bug:{bug.id}",
            )
            for bug in related_bugs
        ]

        rows: list[CoverageMatrixRow] = []
        criteria = user_story.acceptance_criteria
        if not criteria:
            # No AC → single uncovered story-intent row.
            rows.append(
                CoverageMatrixRow(
                    ac_id="STORY-INTENT",
                    ac_text=user_story.title,
                    status=CoverageStatus.UNCOVERED,
                    explanation="No acceptance criteria to map; treat story title as uncovered intent",
                )
            )
            return rows

        for ac in criteria:
            ac_id = ac.id or f"AC-{ac.order}"
            ac_scenario = ScenarioText.from_parts(
                title=ac.text,
                steps=[],
                expected_results=[ac.text],
                ac_texts=[ac.text],
                key=ac_id,
            )

            best_tc_id: int | None = None
            best_tc_score = 0.0
            for tc_scenario in test_scenarios:
                score = self._scorer.score(ac_scenario, tc_scenario)
                if score > best_tc_score:
                    best_tc_score = score
                    best_tc_id = tc_scenario.source_id

            best_bug_id: int | None = None
            best_bug_score = 0.0
            for bug_scenario in bug_scenarios:
                score = self._scorer.score(ac_scenario, bug_scenario)
                if score > best_bug_score:
                    best_bug_score = score
                    best_bug_id = bug_scenario.source_id

            if best_bug_id is not None and best_bug_score >= self._covered_threshold:
                rows.append(
                    CoverageMatrixRow(
                        ac_id=ac_id,
                        ac_text=ac.text,
                        status=CoverageStatus.COVERED_BY_BUG,
                        similarity=best_bug_score,
                        matched_bug_ids=[best_bug_id],
                        matched_test_case_ids=[best_tc_id] if best_tc_id else [],
                        explanation=(
                            f"Covered by related bug {best_bug_id} "
                            f"(similarity {best_bug_score:.2f})"
                        ),
                    )
                )
            elif best_tc_id is not None and best_tc_score >= self._covered_threshold:
                rows.append(
                    CoverageMatrixRow(
                        ac_id=ac_id,
                        ac_text=ac.text,
                        status=CoverageStatus.COVERED_BY_TEST,
                        similarity=best_tc_score,
                        matched_test_case_ids=[best_tc_id],
                        explanation=(
                            f"Covered by test case {best_tc_id} "
                            f"(similarity {best_tc_score:.2f})"
                        ),
                    )
                )
            elif (
                best_tc_id is not None
                and self._partial_threshold <= best_tc_score < self._covered_threshold
            ):
                rows.append(
                    CoverageMatrixRow(
                        ac_id=ac_id,
                        ac_text=ac.text,
                        status=CoverageStatus.PARTIAL,
                        similarity=best_tc_score,
                        matched_test_case_ids=[best_tc_id],
                        explanation=(
                            f"Partial coverage by test case {best_tc_id} "
                            f"(similarity {best_tc_score:.2f}); treat as uncovered gap"
                        ),
                    )
                )
            else:
                rows.append(
                    CoverageMatrixRow(
                        ac_id=ac_id,
                        ac_text=ac.text,
                        status=CoverageStatus.UNCOVERED,
                        similarity=max(best_tc_score, best_bug_score),
                        matched_test_case_ids=[best_tc_id] if best_tc_id else [],
                        matched_bug_ids=[best_bug_id] if best_bug_id else [],
                        explanation="No sufficient test or bug coverage found",
                    )
                )
        return rows

    def identify_uncovered_scenarios(
        self,
        matrix: list[CoverageMatrixRow],
    ) -> list[ScenarioRef]:
        """Return only uncovered (and partial) requirement scenarios.

        Partial rows are included because they still represent requirement gaps
        that need new or updated coverage — not fully covered.
        """
        uncovered: list[ScenarioRef] = []
        for row in matrix:
            if row.status in {CoverageStatus.UNCOVERED, CoverageStatus.PARTIAL}:
                uncovered.append(
                    ScenarioRef(
                        key=row.ac_id,
                        title=row.ac_text,
                        source=ScenarioSource.MISSING,
                        related_ids=row.matched_test_case_ids or row.matched_bug_ids,
                    )
                )
        return uncovered


def _split_lines(text: str | None) -> list[str]:
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]
