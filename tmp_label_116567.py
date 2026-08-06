"""Apply Rule 13 Critical/Regression labels to US 116567 curated drafts."""
from __future__ import annotations

import asyncio
import json
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from qa_intelligence.mcp.tools.create_test_cases import create_test_cases

US = 116567
CASES_PATH = Path("tmp_drafts_116567_curated.json")
MD_PATH = Path("tmp_drafts_116567_curated.md")
LABELS_PATH = Path("tmp_out_116567_labels.json")

# Hand-picked by business impact (1-based). Critical first, then Regression.
CRITICAL = [1, 6, 9, 12, 15]
REGRESSION = [16, 17, 23, 24, 27, 28, 29, 33, 35, 38, 39, 40, 41, 43, 44]


def main() -> None:
    raw = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    # Strip any prior label field for clean base
    cases = [
        {
            "title": c["title"],
            "steps": c["steps"],
            "expected_results": c["expected_results"],
        }
        for c in raw
    ]
    n = len(cases)
    reg_n = int(n * 0.30 + 0.5)
    crit_n = int(n * 0.10 + 0.5)
    if len(CRITICAL) != crit_n or len(REGRESSION) != reg_n:
        raise SystemExit(
            f"Pick counts mismatch: need critical={crit_n} regression={reg_n}, "
            f"got {len(CRITICAL)}/{len(REGRESSION)}"
        )
    if set(CRITICAL) & set(REGRESSION):
        raise SystemExit("Critical and Regression overlap")

    labels = {
        i: (
            "Critical"
            if i in CRITICAL
            else "Regression"
            if i in REGRESSION
            else "Standard"
        )
        for i in range(1, n + 1)
    }

    enriched = [{**c, "label": labels[i]} for i, c in enumerate(cases, 1)]
    CASES_PATH.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")

    LABELS_PATH.write_text(
        json.dumps(
            {
                "user_story_id": US,
                "total": n,
                "targets": {
                    "regression": reg_n,
                    "critical": crit_n,
                    "standard": n - reg_n - crit_n,
                },
                "critical_tc_numbers": CRITICAL,
                "regression_tc_numbers": REGRESSION,
                "by_tc": {str(k): v for k, v in labels.items()},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    md: list[str] = [
        "STORY: FracPro Live+- Minifrac- Update Closure Parameters on Dragging Closure Line",
        f"US: {US}",
        f"COUNT: {n}",
        "NOTE: Dry-run curated drafts — not uploaded to ADO",
        r"SOURCE: AC (4 Scenario blocks) + D:\Live_Plus_UAT (stub) + Minifrac scan",
        "COMPLEXITY: complex (Rule 11 → ~50)",
        "RULE 13 MIX: Critical 10% / Regression 30% (assigned after generation by impact)",
        (
            f"LABELS: Critical={crit_n} ("
            + ", ".join(f"TC-{i}" for i in CRITICAL)
            + f"); Regression={reg_n} ("
            + ", ".join(f"TC-{i}" for i in REGRESSION)
            + ")"
        ),
        "---",
        "",
        "## Label summary",
        "",
        f"### Critical (10% = {crit_n})",
    ]
    for i in CRITICAL:
        md.append(f"- TC-{i}: {cases[i - 1]['title']}")
    md.append("")
    md.append(f"### Regression (30% = {reg_n})")
    for i in REGRESSION:
        md.append(f"- TC-{i}: {cases[i - 1]['title']}")
    md.append("")
    md.append(f"### Standard (60% = {n - reg_n - crit_n})")
    for i in range(1, n + 1):
        if labels[i] == "Standard":
            md.append(f"- TC-{i}: {cases[i - 1]['title']}")
    md.extend(["", "---", ""])

    for i, c in enumerate(cases, 1):
        md.append(f"### TC-{i}: {c['title']}")
        md.append(f"**Label:** {labels[i]}")
        md.append("**Steps**")
        for j, s in enumerate(c["steps"], 1):
            md.append(f"{j}. {s}")
        md.append("**Expected Results**")
        for j, e in enumerate(c["expected_results"], 1):
            md.append(f"{j}. {e}")
        md.append("")

    MD_PATH.write_text("\n".join(md), encoding="utf-8")
    print(f"total={n} critical={crit_n} regression={reg_n}")
    print("Critical:", CRITICAL)
    print("Regression:", REGRESSION)
    print(f"wrote {MD_PATH} and {CASES_PATH}")


async def dry_run() -> None:
    raw = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    payload = [
        {
            "title": c["title"],
            "steps": c["steps"],
            "expected_results": c["expected_results"],
        }
        for c in raw
    ]
    result = await create_test_cases(
        test_cases=payload, dry_run=True, user_story_id=US
    )
    data = result.get("data") or []
    print(
        "dry_run",
        result.get("ok"),
        Counter(x.get("status") for x in data)
        if isinstance(data, list)
        else result.get("error"),
    )


if __name__ == "__main__":
    main()
    asyncio.run(dry_run())
