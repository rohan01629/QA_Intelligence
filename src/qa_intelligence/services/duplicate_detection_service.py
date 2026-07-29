"""DuplicateDetectionService — semantic scenario comparison and classification.

Classifies scenarios into Duplicate / Covered / Needs Update / Generate New.
Also surfaces similar, obsolete, and bug-covered scenarios.

Does NOT generate test cases.
"""

from __future__ import annotations

import structlog

from qa_intelligence.domain.enums import DuplicateBasis, ScenarioDisposition, ScenarioSource
from qa_intelligence.domain.models.bug import Bug
from qa_intelligence.domain.models.coverage import ScenarioRef
from qa_intelligence.domain.models.detection import DuplicateDetectionResult, ScenarioMatch
from qa_intelligence.domain.models.duplicate import DuplicateAnalysis, DuplicateCluster
from qa_intelligence.domain.models.read_models import TestCaseSummary
from qa_intelligence.domain.models.user_story import UserStory
from qa_intelligence.domain.similarity import (
    FeatureSimilarityScorer,
    ScenarioText,
    SimilarityScorer,
)

logger = structlog.get_logger(__name__)


class DuplicateDetectionService:
    """Detect duplicates, coverage, obsolete tests, and bug-covered scenarios."""

    def __init__(
        self,
        *,
        scorer: SimilarityScorer | None = None,
        duplicate_threshold: float = 0.82,
        similar_threshold: float = 0.65,
        covered_threshold: float = 0.72,
        needs_update_threshold: float = 0.50,
        obsolete_threshold: float = 0.40,
    ) -> None:
        self._scorer = scorer or FeatureSimilarityScorer()
        self._duplicate_threshold = duplicate_threshold
        self._similar_threshold = similar_threshold
        self._covered_threshold = covered_threshold
        self._needs_update_threshold = needs_update_threshold
        self._obsolete_threshold = obsolete_threshold

    def detect(
        self,
        user_story: UserStory,
        existing_test_cases: list[TestCaseSummary],
        related_bugs: list[Bug] | None = None,
    ) -> DuplicateDetectionResult:
        """Run semantic comparison and return disposition buckets."""
        related_bugs = related_bugs or []
        ac_texts = [ac.text for ac in user_story.acceptance_criteria]
        ac_scenario_texts = self._ac_scenarios(user_story)
        test_scenario_texts = [
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
        bug_scenario_texts = [
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

        clusters = self._cluster_duplicates(test_scenario_texts)
        duplicate_matches = self._matches_from_clusters(clusters)

        covered: list[ScenarioMatch] = []
        needs_update: list[ScenarioMatch] = []
        generate_new: list[ScenarioMatch] = []
        similar: list[ScenarioMatch] = []
        obsolete: list[ScenarioMatch] = []
        bug_covered: list[ScenarioMatch] = []

        covered_ac_keys: set[str] = set()
        bug_covered_ac_keys: set[str] = set()

        # Map each AC intent to best existing test case.
        for ac_scenario in ac_scenario_texts:
            best_tc: ScenarioText | None = None
            best_score = 0.0
            for tc_scenario in test_scenario_texts:
                score = self._scorer.score(ac_scenario, tc_scenario)
                if score > best_score:
                    best_score = score
                    best_tc = tc_scenario

            best_bug: ScenarioText | None = None
            best_bug_score = 0.0
            for bug_scenario in bug_scenario_texts:
                score = self._scorer.score(ac_scenario, bug_scenario)
                if score > best_bug_score:
                    best_bug_score = score
                    best_bug = bug_scenario

            if best_bug is not None and best_bug_score >= self._covered_threshold:
                match = ScenarioMatch(
                    key=ac_scenario.key,
                    title=ac_scenario.title,
                    disposition=ScenarioDisposition.COVERED,
                    similarity=best_bug_score,
                    basis=self._basis_from_explain(ac_scenario, best_bug),
                    matched_bug_ids=[best_bug.source_id]
                    if best_bug.source_id
                    else [],
                    related_ac_ids=[ac_scenario.key],
                    explanation=(
                        f"Bug-covered by semantic match to bug "
                        f"{best_bug.source_id} ({best_bug_score:.2f})"
                    ),
                    is_bug_covered=True,
                )
                bug_covered.append(match)
                covered.append(match)
                bug_covered_ac_keys.add(ac_scenario.key)
                covered_ac_keys.add(ac_scenario.key)
                continue

            if best_tc is not None and best_score >= self._covered_threshold:
                match = ScenarioMatch(
                    key=ac_scenario.key,
                    title=ac_scenario.title,
                    disposition=ScenarioDisposition.COVERED,
                    similarity=best_score,
                    basis=self._basis_from_explain(ac_scenario, best_tc),
                    matched_test_case_ids=[best_tc.source_id]
                    if best_tc.source_id
                    else [],
                    related_ac_ids=[ac_scenario.key],
                    explanation=(
                        f"Covered by existing test case {best_tc.source_id} "
                        f"(similarity {best_score:.2f})"
                    ),
                )
                covered.append(match)
                covered_ac_keys.add(ac_scenario.key)
                if (
                    self._similar_threshold <= best_score < self._duplicate_threshold
                ):
                    similar.append(
                        match.model_copy(
                            update={
                                "is_similar": True,
                                "explanation": (
                                    f"Similar to test case {best_tc.source_id} "
                                    f"at {best_score:.2f}"
                                ),
                            }
                        )
                    )
                continue

            if (
                best_tc is not None
                and self._needs_update_threshold <= best_score < self._covered_threshold
            ):
                match = ScenarioMatch(
                    key=ac_scenario.key,
                    title=ac_scenario.title,
                    disposition=ScenarioDisposition.NEEDS_UPDATE,
                    similarity=best_score,
                    basis=self._basis_from_explain(ac_scenario, best_tc),
                    matched_test_case_ids=[best_tc.source_id]
                    if best_tc.source_id
                    else [],
                    related_ac_ids=[ac_scenario.key],
                    explanation=(
                        f"Existing test case {best_tc.source_id} is related but "
                        f"outdated/incomplete (similarity {best_score:.2f})"
                    ),
                    is_similar=True,
                )
                needs_update.append(match)
                similar.append(match)
                continue

            generate_new.append(
                ScenarioMatch(
                    key=ac_scenario.key,
                    title=ac_scenario.title,
                    disposition=ScenarioDisposition.GENERATE_NEW,
                    similarity=best_score,
                    related_ac_ids=[ac_scenario.key],
                    explanation=(
                        "No sufficiently similar existing test case or bug coverage found"
                    ),
                )
            )

        # Obsolete: existing tests weakly related to all current AC intents.
        for tc_scenario in test_scenario_texts:
            if not ac_scenario_texts:
                # Without AC, cannot mark obsolete reliably.
                continue
            best_ac_score = max(
                (self._scorer.score(tc_scenario, ac) for ac in ac_scenario_texts),
                default=0.0,
            )
            if best_ac_score < self._obsolete_threshold:
                obsolete_match = ScenarioMatch(
                    key=tc_scenario.key,
                    title=tc_scenario.title,
                    disposition=ScenarioDisposition.NEEDS_UPDATE,
                    similarity=best_ac_score,
                    matched_test_case_ids=[tc_scenario.source_id]
                    if tc_scenario.source_id
                    else [],
                    explanation=(
                        f"Existing test case appears obsolete vs current AC "
                        f"(best similarity {best_ac_score:.2f})"
                    ),
                    is_obsolete=True,
                )
                obsolete.append(obsolete_match)
                needs_update.append(obsolete_match)

        # Similar pairs among existing tests below duplicate threshold.
        for left_idx, left in enumerate(test_scenario_texts):
            for right in test_scenario_texts[left_idx + 1 :]:
                score = self._scorer.score(left, right)
                if self._similar_threshold <= score < self._duplicate_threshold:
                    similar.append(
                        ScenarioMatch(
                            key=f"similar:{left.key}:{right.key}",
                            title=f"{left.title} ≈ {right.title}",
                            disposition=ScenarioDisposition.DUPLICATE,
                            similarity=score,
                            basis=self._basis_from_explain(left, right),
                            matched_test_case_ids=[
                                i
                                for i in (left.source_id, right.source_id)
                                if i is not None
                            ],
                            explanation=(
                                f"Similar scenarios (not full duplicates) at {score:.2f}"
                            ),
                            is_similar=True,
                        )
                    )

        result = DuplicateDetectionResult(
            user_story_id=user_story.id,
            duplicate=duplicate_matches,
            covered=covered,
            needs_update=needs_update,
            generate_new=generate_new,
            similar=similar,
            obsolete=obsolete,
            bug_covered=bug_covered,
            clusters=clusters,
            duplicate_threshold=self._duplicate_threshold,
            similar_threshold=self._similar_threshold,
            covered_threshold=self._covered_threshold,
        )

        logger.info(
            "duplicate.detection_completed",
            user_story_id=user_story.id,
            duplicate=len(result.duplicate),
            covered=len(result.covered),
            needs_update=len(result.needs_update),
            generate_new=len(result.generate_new),
            similar=len(result.similar),
            obsolete=len(result.obsolete),
            bug_covered=len(result.bug_covered),
        )
        return result

    def detect_duplicate_clusters(
        self,
        candidates: list[TestCaseSummary],
        existing: list[TestCaseSummary],
    ) -> DuplicateAnalysis:
        """Cluster duplicates across candidate + existing inventories."""
        scenarios = [
            ScenarioText.from_parts(
                title=tc.title,
                steps=tc.steps,
                expected_results=tc.expected_results,
                source_id=tc.id,
                key=f"tc:{tc.id}",
            )
            for tc in [*candidates, *existing]
        ]
        clusters = self._cluster_duplicates(scenarios)
        return DuplicateAnalysis.from_clusters(
            clusters=clusters,
            threshold=self._duplicate_threshold,
        )

    def _ac_scenarios(self, story: UserStory) -> list[ScenarioText]:
        scenarios: list[ScenarioText] = []
        for ac in story.acceptance_criteria:
            key = ac.id or f"AC-{ac.order}"
            scenarios.append(
                ScenarioText.from_parts(
                    title=ac.text,
                    steps=[],
                    expected_results=[ac.text],
                    ac_texts=[ac.text],
                    key=key,
                )
            )
        if not scenarios:
            # Fall back to story title as a single intent when AC missing.
            scenarios.append(
                ScenarioText.from_parts(
                    title=story.title,
                    steps=[],
                    expected_results=[],
                    ac_texts=[story.title, story.description],
                    key="STORY-INTENT",
                )
            )
        return scenarios

    def _cluster_duplicates(
        self,
        scenarios: list[ScenarioText],
    ) -> list[DuplicateCluster]:
        parent = list(range(len(scenarios)))

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def union(i: int, j: int) -> None:
            ri, rj = find(i), find(j)
            if ri != rj:
                parent[rj] = ri

        pair_meta: dict[tuple[int, int], tuple[float, DuplicateBasis, str]] = {}
        for i, left in enumerate(scenarios):
            for j in range(i + 1, len(scenarios)):
                right = scenarios[j]
                score = self._scorer.score(left, right)
                if score >= self._duplicate_threshold:
                    union(i, j)
                    basis = self._basis_from_explain(left, right)
                    pair_meta[(i, j)] = (
                        score,
                        basis,
                        self._scorer.explain_basis(left, right),
                    )

        groups: dict[int, list[int]] = {}
        for idx in range(len(scenarios)):
            root = find(idx)
            groups.setdefault(root, []).append(idx)

        clusters: list[DuplicateCluster] = []
        for members in groups.values():
            if len(members) < 2:
                continue
            members_sorted = sorted(members)
            canonical_idx = members_sorted[0]
            canonical = scenarios[canonical_idx]
            duplicates = [scenarios[i] for i in members_sorted[1:]]
            # Representative pair score
            score = 0.0
            basis = DuplicateBasis.INTENT
            explanation = ""
            for i in members_sorted:
                for j in members_sorted:
                    if i >= j:
                        continue
                    meta = pair_meta.get((i, j)) or pair_meta.get((j, i))
                    if meta and meta[0] >= score:
                        score, basis, explanation = meta

            clusters.append(
                DuplicateCluster(
                    canonical=ScenarioRef(
                        key=canonical.key,
                        title=canonical.title,
                        source=ScenarioSource.EXISTING,
                        related_ids=[canonical.source_id]
                        if canonical.source_id
                        else [],
                    ),
                    duplicates=[
                        ScenarioRef(
                            key=item.key,
                            title=item.title,
                            source=ScenarioSource.EXISTING,
                            related_ids=[item.source_id] if item.source_id else [],
                        )
                        for item in duplicates
                    ],
                    similarity=score,
                    basis=basis,
                    explanation=explanation,
                )
            )
        return clusters

    def _matches_from_clusters(
        self,
        clusters: list[DuplicateCluster],
    ) -> list[ScenarioMatch]:
        matches: list[ScenarioMatch] = []
        for cluster in clusters:
            related_ids = list(cluster.canonical.related_ids)
            for dup in cluster.duplicates:
                related_ids.extend(dup.related_ids)
                matches.append(
                    ScenarioMatch(
                        key=dup.key,
                        title=dup.title,
                        disposition=ScenarioDisposition.DUPLICATE,
                        similarity=cluster.similarity,
                        basis=cluster.basis,
                        matched_test_case_ids=related_ids,
                        explanation=(
                            f"Duplicate of '{cluster.canonical.title}' "
                            f"({cluster.similarity:.2f}; {cluster.basis.value})"
                        ),
                    )
                )
        return matches

    def _basis_from_explain(
        self,
        left: ScenarioText,
        right: ScenarioText,
    ) -> DuplicateBasis:
        explanation = self._scorer.explain_basis(left, right)
        if "basis=workflow" in explanation:
            return DuplicateBasis.WORKFLOW
        if "basis=expected_result" in explanation:
            return DuplicateBasis.EXPECTED_RESULT
        if left.ac_tokens and right.ac_tokens:
            # mild AC preference when both have AC tokens and title is strong
            return DuplicateBasis.AC_MAPPING
        return DuplicateBasis.INTENT


def _split_lines(text: str | None) -> list[str]:
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]
