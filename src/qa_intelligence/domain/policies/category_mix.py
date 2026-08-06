"""Rule 13 — decide Regression / Sanity during generation, then mark.

Flow:
  1. Before drafting, plan the suite: which TCs are Regression (~30%),
     which are Critical/Sanity (~10%), and which are Standard.
  2. Generate each TC for that decided role (category + content intent).
  3. Stamp ADO toggles from that decision (IsRegression / Sanity).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from qa_intelligence.domain.enums import ScenarioSource, TestCategory
from qa_intelligence.domain.models.coverage import ScenarioRef
from qa_intelligence.domain.models.generation import GeneratedTestCaseRecord
from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.domain.policies.product_rules import (
    CRITICAL_MIX_RATIO,
    REGRESSION_MIX_RATIO,
)

_REGRESSION_HINTS = (
    "adjacent",
    "neighbor",
    "unchanged",
    "regression",
    "baseline",
    "previously working",
    "other button",
    "word report",
    "witsml",
    "save button",
    "remains stable",
    "not broken",
    "parity",
    "existing workflow",
    "still works",
    "still holds",
    "ci-reg",
)
_SANITY_HINTS = (
    "data loss",
    "corrupt",
    "command",
    "permission",
    "operator",
    "unauthorized",
    "security",
    "auth",
    "blocking",
    "critical",
    "must not",
    "shall not",
    "destructive",
    "sanity",
    "smoke",
    "reject",
    "prevent",
    "fail",
)


class MixSlotKind(StrEnum):
    REGRESSION = "regression"
    CRITICAL = "critical"
    STANDARD = "standard"


@dataclass(frozen=True)
class MixTargets:
    """Rule 13 planned counts for a suite of ``total`` cases."""

    total: int
    regression: int
    critical: int
    standard: int
    regression_selected: int = 0
    critical_selected: int = 0


@dataclass(frozen=True)
class GenerationPlanItem:
    """One planned TC: scenario + category + Rule 13 role."""

    scenario: ScenarioRef
    category: TestCategory
    mix_kind: MixSlotKind


def ado_flags_for_mix_kind(mix_kind: str) -> tuple[bool, bool]:
    """Map Rule 13 mix to ADO toggles: (is_regression, is_sanity)."""
    if mix_kind == MixSlotKind.CRITICAL.value:
        return False, True
    if mix_kind == MixSlotKind.REGRESSION.value:
        return True, False
    return False, False


def stamp_mix_flags_on_case(case: TestCase, mix_kind: str) -> TestCase:
    """Apply Rule 13 mix flags onto a TestCase for ADO create."""
    is_regression, is_sanity = ado_flags_for_mix_kind(mix_kind)
    return case.model_copy(
        update={"is_regression": is_regression, "is_sanity": is_sanity}
    )


def compute_mix_targets(total: int) -> MixTargets:
    """Return Rule 13 planned counts (~30% Regression / ~10% Critical)."""
    n = max(int(total), 0)
    if n == 0:
        return MixTargets(total=0, regression=0, critical=0, standard=0)

    regression = int(n * REGRESSION_MIX_RATIO + 0.5)
    critical = int(n * CRITICAL_MIX_RATIO + 0.5)

    if n >= 4 and regression == 0:
        regression = 1
    if n >= 10 and critical == 0:
        critical = 1

    if regression + critical > n:
        overflow = regression + critical - n
        trim_crit = min(critical, overflow)
        critical -= trim_crit
        overflow -= trim_crit
        regression = max(0, regression - overflow)

    standard = n - regression - critical
    return MixTargets(
        total=n,
        regression=regression,
        critical=critical,
        standard=standard,
    )


def _spaced_indices(total: int, count: int) -> list[int]:
    """Spread ``count`` slot indices across ``total`` positions."""
    if count <= 0 or total <= 0:
        return []
    if count >= total:
        return list(range(total))
    return [min(total - 1, int((i + 0.5) * total / count)) for i in range(count)]


def _scenario_blob(scenario: ScenarioRef) -> str:
    return f"{scenario.key} {scenario.title}".lower()


def score_scenario_regression(scenario: ScenarioRef) -> float:
    """How suitable is this scenario as a Regression TC."""
    blob = _scenario_blob(scenario)
    score = 0.0
    key = (scenario.key or "").upper()
    if key.startswith("CI-REG") or "REGRESSION" in key or key.startswith("REG"):
        score += 5.0
    score += sum(1.5 for hint in _REGRESSION_HINTS if hint in blob)
    if re.search(r"\b(adjacent|neighbor|baseline|witsml|word|save)\b", blob):
        score += 2.0
    return score


def score_scenario_sanity(scenario: ScenarioRef) -> float:
    """How suitable is this scenario as a Critical / Sanity TC."""
    blob = _scenario_blob(scenario)
    score = 0.0
    score += sum(1.75 for hint in _SANITY_HINTS if hint in blob)
    if re.search(r"\b(shall not|must not|permission|unauthorized|operator|block)\b", blob):
        score += 3.0
    if re.search(r"\b(critical|sanity|smoke|data loss)\b", blob):
        score += 3.0
    return score


def _pick_category(
    allowed: list[TestCategory],
    preferred: list[TestCategory],
) -> TestCategory:
    for category in preferred:
        if category in allowed:
            return category
    return allowed[0] if allowed else TestCategory.POSITIVE


def plan_suite_mix(
    budget: int,
    scenarios: list[ScenarioRef],
    allowed_categories: list[TestCategory],
) -> tuple[list[GenerationPlanItem], MixTargets]:
    """Decide which planned TCs are Regression vs Sanity vs Standard.

    Called **before** drafting so generation produces the right kind of case
    for each role, then ADO toggles follow that decision (Rule 13).
    """
    n = max(int(budget), 0)
    targets = compute_mix_targets(n)
    if n == 0 or not scenarios:
        return [], targets

    allowed = list(allowed_categories) or list(
        [
            TestCategory.POSITIVE,
            TestCategory.NEGATIVE,
            TestCategory.EDGE,
            TestCategory.VALIDATION,
            TestCategory.REGRESSION,
        ]
    )
    sanity_category = _pick_category(
        allowed,
        [
            TestCategory.PERMISSION,
            TestCategory.SECURITY,
            TestCategory.NEGATIVE,
            TestCategory.VALIDATION,
        ],
    )
    regression_category = _pick_category(
        allowed,
        [TestCategory.REGRESSION, TestCategory.POSITIVE],
    )
    standard_categories = [c for c in allowed if c != regression_category] or allowed

    by_sanity = sorted(
        range(len(scenarios)),
        key=lambda i: (-score_scenario_sanity(scenarios[i]), i),
    )
    by_regression = sorted(
        range(len(scenarios)),
        key=lambda i: (-score_scenario_regression(scenarios[i]), i),
    )

    roles: list[MixSlotKind] = [MixSlotKind.STANDARD] * n
    for idx in _spaced_indices(n, targets.critical):
        roles[idx] = MixSlotKind.CRITICAL
    taken = {i for i, role in enumerate(roles) if role == MixSlotKind.CRITICAL}
    reg_slots = [i for i in _spaced_indices(n, targets.regression + targets.critical) if i not in taken]
    # Prefer dedicated regression spacing when possible.
    reg_only = [i for i in _spaced_indices(n, targets.regression) if i not in taken]
    use_reg = reg_only if len(reg_only) >= targets.regression else reg_slots
    for idx in use_reg[: targets.regression]:
        roles[idx] = MixSlotKind.REGRESSION

    sanity_cursor = 0
    regression_cursor = 0
    standard_cursor = 0
    plan: list[GenerationPlanItem] = []
    for position, role in enumerate(roles):
        if role == MixSlotKind.CRITICAL:
            scenario = scenarios[by_sanity[sanity_cursor % len(scenarios)]]
            sanity_cursor += 1
            plan.append(
                GenerationPlanItem(
                    scenario=scenario,
                    category=sanity_category,
                    mix_kind=MixSlotKind.CRITICAL,
                )
            )
        elif role == MixSlotKind.REGRESSION:
            scenario = scenarios[by_regression[regression_cursor % len(scenarios)]]
            regression_cursor += 1
            plan.append(
                GenerationPlanItem(
                    scenario=scenario,
                    category=regression_category,
                    mix_kind=MixSlotKind.REGRESSION,
                )
            )
        else:
            scenario = scenarios[position % len(scenarios)]
            category = standard_categories[standard_cursor % len(standard_categories)]
            standard_cursor += 1
            plan.append(
                GenerationPlanItem(
                    scenario=scenario,
                    category=category,
                    mix_kind=MixSlotKind.STANDARD,
                )
            )
    return plan, targets


def summarize_mix_from_records(
    records: list[GeneratedTestCaseRecord],
) -> tuple[MixTargets, list[int], list[int]]:
    """Recount Rule 13 decisions already stamped during generation."""
    accepted = [r for r in records if not r.rejected and r.test_case is not None]
    ceilings = compute_mix_targets(len(accepted))
    regression_ids: list[int] = []
    critical_ids: list[int] = []
    for tc_num, record in enumerate(accepted, start=1):
        if record.mix_kind == MixSlotKind.REGRESSION.value:
            regression_ids.append(tc_num)
        if record.is_critical or record.mix_kind == MixSlotKind.CRITICAL.value:
            critical_ids.append(tc_num)
    targets = MixTargets(
        total=ceilings.total,
        regression=ceilings.regression,
        critical=ceilings.critical,
        standard=ceilings.total - len(regression_ids) - len(critical_ids),
        regression_selected=len(regression_ids),
        critical_selected=len(critical_ids),
    )
    return targets, regression_ids, critical_ids


def classify_mix_for_records(
    records: list[GeneratedTestCaseRecord],
) -> tuple[list[GeneratedTestCaseRecord], MixTargets, list[int], list[int]]:
    """Finalize stamps from generation-time mix_kind decisions.

    If a record already has a mix role from planning, keep it and stamp ADO
    flags. Does not re-assign roles by post-hoc scoring.
    """
    updated: list[GeneratedTestCaseRecord] = []
    for record in records:
        if record.rejected or record.test_case is None:
            updated.append(
                record.model_copy(
                    update={"mix_kind": MixSlotKind.STANDARD.value, "is_critical": False}
                )
            )
            continue
        mix_kind = record.mix_kind or MixSlotKind.STANDARD.value
        if mix_kind not in {
            MixSlotKind.REGRESSION.value,
            MixSlotKind.CRITICAL.value,
            MixSlotKind.STANDARD.value,
        }:
            mix_kind = MixSlotKind.STANDARD.value
        is_critical = mix_kind == MixSlotKind.CRITICAL.value
        stamped = stamp_mix_flags_on_case(record.test_case, mix_kind)
        updated.append(
            record.model_copy(
                update={
                    "mix_kind": mix_kind,
                    "is_critical": is_critical,
                    "test_case": stamped,
                }
            )
        )
    targets, regression_ids, critical_ids = summarize_mix_from_records(updated)
    return updated, targets, regression_ids, critical_ids


# Kept for tests / callers that score drafted records.
def score_regression_fitness(record: GeneratedTestCaseRecord) -> float:
    if record.test_case is None or record.rejected:
        return -1.0
    scenario = ScenarioRef(
        key=record.source_scenario_key,
        title=record.test_case.title,
        source=ScenarioSource.MISSING,
    )
    score = score_scenario_regression(scenario)
    if record.category == TestCategory.REGRESSION:
        score += 4.0
    return score


def score_critical_fitness(record: GeneratedTestCaseRecord) -> float:
    if record.test_case is None or record.rejected:
        return -1.0
    scenario = ScenarioRef(
        key=record.source_scenario_key,
        title=record.test_case.title,
        source=ScenarioSource.MISSING,
    )
    score = score_scenario_sanity(scenario)
    if record.category in {
        TestCategory.NEGATIVE,
        TestCategory.SECURITY,
        TestCategory.PERMISSION,
    }:
        score += 3.5
    return score


def build_generation_slots(
    total: int,
    categories: list[TestCategory],
) -> list[object]:
    """Deprecated alias — planning is via ``plan_suite_mix``."""
    _ = (total, categories)
    return []
