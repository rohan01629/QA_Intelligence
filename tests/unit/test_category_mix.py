"""Unit tests for Rule 13 generation-time mix planning."""

from __future__ import annotations

from qa_intelligence.domain.enums import ScenarioSource, TestCategory
from qa_intelligence.domain.models.coverage import ScenarioRef
from qa_intelligence.domain.models.generation import GeneratedTestCaseRecord
from qa_intelligence.domain.models.test_case import TestCase
from qa_intelligence.domain.models.validation import ValidationResult
from qa_intelligence.domain.policies.category_mix import (
    MixSlotKind,
    classify_mix_for_records,
    compute_mix_targets,
    plan_suite_mix,
    score_critical_fitness,
    score_regression_fitness,
)
from qa_intelligence.domain.policies.product_rules import PRODUCT_RULES


def test_product_rules_include_rule_13() -> None:
    assert len(PRODUCT_RULES) == 13
    assert "30%" in PRODUCT_RULES[12]
    assert "10%" in PRODUCT_RULES[12]
    assert "decide" in PRODUCT_RULES[12].lower()


def test_mix_targets_for_25() -> None:
    mix = compute_mix_targets(25)
    assert mix.total == 25
    assert mix.regression == 8
    assert mix.critical == 3
    assert mix.regression + mix.critical + mix.standard == 25


def test_mix_targets_for_50() -> None:
    mix = compute_mix_targets(50)
    assert mix.regression == 15
    assert mix.critical == 5
    assert mix.standard == 30


def _scenario(key: str, title: str) -> ScenarioRef:
    return ScenarioRef(key=key, title=title, source=ScenarioSource.MISSING)


def _record(
    *,
    key: str,
    category: TestCategory,
    title: str,
    mix_kind: str = MixSlotKind.STANDARD.value,
    steps: list[str] | None = None,
) -> GeneratedTestCaseRecord:
    step_list = steps or ["Step one", "Step two"]
    case = TestCase(
        title=title,
        steps=step_list,
        expected_results=[f"Expected {i}" for i in range(1, len(step_list) + 1)],
    )
    return GeneratedTestCaseRecord(
        source_scenario_key=key,
        category=category,
        test_case=case,
        validation=ValidationResult.success(),
        rejected=False,
        mix_kind=mix_kind,
        is_critical=mix_kind == MixSlotKind.CRITICAL.value,
    )


def test_plan_suite_mix_decides_roles_before_generate() -> None:
    scenarios = [
        _scenario("AC-SEC", "Verify permission guard blocks unauthorized access"),
        _scenario("CI-REG-1", "Verify adjacent WITSML workflow remains stable"),
        _scenario("AC-UI", "Verify button label"),
        _scenario("AC-POS", "Verify happy path open"),
        _scenario("CI-REG-2", "Verify neighbor Save button unchanged"),
        _scenario("AC-NEG", "Verify unauthorized operator shall not invoke command"),
        _scenario("AC-EDGE", "Verify empty state"),
        _scenario("AC-API", "Verify API status"),
        _scenario("CI-REG-3", "Verify Word report baseline still works"),
        _scenario("AC-VAL", "Verify invalid input is rejected"),
    ]
    allowed = [
        TestCategory.POSITIVE,
        TestCategory.NEGATIVE,
        TestCategory.EDGE,
        TestCategory.VALIDATION,
        TestCategory.REGRESSION,
        TestCategory.PERMISSION,
    ]
    plan, targets = plan_suite_mix(10, scenarios, allowed)
    assert len(plan) == 10
    assert targets.regression == 3
    assert targets.critical == 1
    assert sum(1 for p in plan if p.mix_kind == MixSlotKind.REGRESSION) == 3
    assert sum(1 for p in plan if p.mix_kind == MixSlotKind.CRITICAL) == 1
    # Sanity role uses a high-risk category; regression uses REGRESSION category.
    sanity = next(p for p in plan if p.mix_kind == MixSlotKind.CRITICAL)
    assert sanity.category in {
        TestCategory.PERMISSION,
        TestCategory.SECURITY,
        TestCategory.NEGATIVE,
        TestCategory.VALIDATION,
    }
    regs = [p for p in plan if p.mix_kind == MixSlotKind.REGRESSION]
    assert all(p.category == TestCategory.REGRESSION for p in regs)


def test_classify_keeps_generation_decisions_and_stamps_flags() -> None:
    records = [
        _record(
            key="CI-REG-1",
            category=TestCategory.REGRESSION,
            title="Verify adjacent workflow",
            mix_kind=MixSlotKind.REGRESSION.value,
        ),
        _record(
            key="AC-NEG",
            category=TestCategory.NEGATIVE,
            title="Verify unauthorized operator blocked",
            mix_kind=MixSlotKind.CRITICAL.value,
        ),
        _record(
            key="AC-UI",
            category=TestCategory.UI,
            title="Verify label",
            mix_kind=MixSlotKind.STANDARD.value,
        ),
    ]
    updated, targets, reg_ids, crit_ids = classify_mix_for_records(records)
    assert targets.regression_selected == 1
    assert targets.critical_selected == 1
    assert reg_ids == [1]
    assert crit_ids == [2]
    assert updated[0].test_case is not None and updated[0].test_case.is_regression
    assert updated[1].test_case is not None and updated[1].test_case.is_sanity
    assert updated[2].test_case is not None
    assert updated[2].test_case.is_regression is False
    assert updated[2].test_case.is_sanity is False


def test_regression_scores_higher_for_adjacent_cases() -> None:
    adj = _record(
        key="CI-REG-1",
        category=TestCategory.REGRESSION,
        title="Verify Word Report button remains unchanged",
        steps=["Open reports", "Click Word Report", "Confirm download still works"],
    )
    plain = _record(
        key="AC-1",
        category=TestCategory.UI,
        title="Verify label text",
        steps=["Open screen", "Read label"],
    )
    assert score_regression_fitness(adj) > score_regression_fitness(plain)


def test_critical_scores_higher_for_permission_guard() -> None:
    crit = _record(
        key="AC-OP",
        category=TestCategory.NEGATIVE,
        title="Verify Operator cannot invoke command",
        steps=["Sign in as Operator", "Attempt action", "Capture rejection"],
    )
    plain = _record(
        key="AC-UI",
        category=TestCategory.UI,
        title="Verify tooltip text",
        steps=["Hover control", "Read tooltip"],
    )
    assert score_critical_fitness(crit) > score_critical_fitness(plain)


def test_ado_flags_for_mix_kind() -> None:
    from qa_intelligence.domain.policies.category_mix import ado_flags_for_mix_kind

    assert ado_flags_for_mix_kind(MixSlotKind.CRITICAL.value) == (False, True)
    assert ado_flags_for_mix_kind(MixSlotKind.REGRESSION.value) == (True, False)
    assert ado_flags_for_mix_kind(MixSlotKind.STANDARD.value) == (False, False)
