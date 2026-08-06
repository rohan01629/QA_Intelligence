"""Fresh TC suite for US 116561 — ASCII Generate with saved channel config + gap analysis."""
from __future__ import annotations

import asyncio
import json
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from qa_intelligence.mcp.tools.create_test_cases import create_test_cases

US = 116561
STORY = "FracPro Live+ Reports - Generate ASCII Report using saved channel configuration"
CODEBASE = r"D:\Live_Plus_QA\fracpro-agile"

CASES: list[dict] = [
    # Scenario 1 — load existing config
    {
        "title": "Verify GET reportSetup loads saved asciirealtime into Real-time channel selections",
        "steps": [
            "Prepare a well whose reportSetup has non-empty asciirealtime values.",
            "Open the ASCII Report dialog.",
            "Inspect Real-time tab selections after load.",
        ],
        "expected_results": [
            "Saved asciirealtime exists in reportSetup.",
            "GET reportSetup is called when the dialog opens.",
            "Real-time checkboxes match saved asciirealtime channel names.",
        ],
    },
    {
        "title": "Verify GET reportSetup loads saved asciifp into FracPro channel selections",
        "steps": [
            "Prepare a well whose reportSetup has non-empty asciifp values.",
            "Open the ASCII Report dialog and open the FracPro tab.",
            "Inspect FracPro tab selections after load.",
        ],
        "expected_results": [
            "Saved asciifp exists in reportSetup.",
            "FracPro channel list is shown.",
            "FracPro checkboxes match saved asciifp channel names.",
        ],
    },
    {
        "title": "Verify missing or empty asciirealtime selects all Real-time channels by default",
        "steps": [
            "Use a well where asciirealtime is missing or empty.",
            "Open the ASCII Report dialog on the Real-time tab.",
            "Check selection state of listed Real-time channels.",
        ],
        "expected_results": [
            "GET reportSetup returns missing or empty asciirealtime.",
            "Real-time channels load.",
            "All Real-time channels are selected by default.",
        ],
    },
    {
        "title": "Verify missing or empty asciifp selects no FracPro channels by default",
        "steps": [
            "Use a well where asciifp is missing or empty.",
            "Open the ASCII Report dialog on the FracPro tab.",
            "Check selection state of listed FracPro channels.",
        ],
        "expected_results": [
            "GET reportSetup returns missing or empty asciifp.",
            "FracPro channels load.",
            "No FracPro channels are selected by default.",
        ],
    },
    # Scenario 2 — generate with updated selection
    {
        "title": "Verify Generate with changed Real-time selection updates asciirealtime then invokes COMMAND",
        "steps": [
            "Open ASCII Report dialog with known saved Real-time selections.",
            "Change one or more Real-time channel checkboxes.",
            "Click Generate and monitor reportSetup update then COMMAND.",
        ],
        "expected_results": [
            "Dialog shows current saved Real-time selections.",
            "Selection differs from initial asciirealtime.",
            "reportSetup update is called with new asciirealtime; after success COMMAND GenerateASCII runs.",
        ],
    },
    {
        "title": "Verify Generate with changed FracPro selection updates asciifp then invokes COMMAND",
        "steps": [
            "Open ASCII Report dialog and change one or more FracPro channel selections.",
            "Click Generate.",
            "Monitor reportSetup update payload and subsequent COMMAND.",
        ],
        "expected_results": [
            "FracPro selections are modified.",
            "reportSetup update includes updated asciifp.",
            "After successful update, COMMAND GenerateASCII is invoked.",
        ],
    },
    {
        "title": "Verify reportSetup update preserves non-ASCII properties when saving channel selection",
        "steps": [
            "Note existing reportSetup non-ASCII fields such as Plots, WarnDupPlots, Options.",
            "Change ASCII channel selections and click Generate.",
            "Inspect the update payload sent to reportSetup.",
        ],
        "expected_results": [
            "Baseline non-ASCII reportSetup values are known.",
            "Generate with changed selections triggers update.",
            "Payload spreads existing reportSetup and only replaces asciirealtime/asciifp.",
        ],
    },
    {
        "title": "Verify COMMAND runs only after successful reportSetup update when selection changed",
        "steps": [
            "Change channel selections in ASCII dialog.",
            "Click Generate and observe call order.",
            "Confirm COMMAND does not start before update success.",
        ],
        "expected_results": [
            "Selections changed.",
            "reportSetup update is issued first.",
            "COMMAND GenerateASCII starts only after update success callback.",
        ],
    },
    {
        "title": "Verify reopening dialog after successful Generate shows last saved channel configuration",
        "steps": [
            "Change selections, Generate successfully, and wait for flow to complete.",
            "Open ASCII Report dialog again.",
            "Compare Real-time and FracPro selections to the values just saved.",
        ],
        "expected_results": [
            "Generate completes with saved configuration.",
            "Dialog reopens and loads reportSetup.",
            "Selections match the last saved asciirealtime and asciifp.",
        ],
    },
    # Scenario 3 — generate without changes
    {
        "title": "Verify Generate with unchanged selections skips reportSetup update and calls COMMAND directly",
        "steps": [
            "Open ASCII Report dialog without changing any channel selections.",
            "Click Generate.",
            "Monitor whether reportSetup update is skipped and COMMAND still runs.",
        ],
        "expected_results": [
            "Dialog opens with current saved selections.",
            "No reportSetup update call is made.",
            "COMMAND GenerateASCII is invoked directly.",
        ],
    },
    {
        "title": "Verify unchanged Generate still completes ASCII report generation via COMMAND",
        "steps": [
            "Open ASCII dialog with unchanged selections and click Generate.",
            "Wait for SignalR/COMMAND GenerateASCII completion.",
            "Confirm ASCII download or success path proceeds.",
        ],
        "expected_results": [
            "Generate starts COMMAND without reportSetup update.",
            "COMMAND/SignalR path runs for GenerateASCII.",
            "ASCII report generation completes or download begins on success.",
        ],
    },
    # Scenario 4 — errors
    {
        "title": "Verify failed reportSetup update shows error and does not invoke COMMAND",
        "steps": [
            "Change channel selections in ASCII dialog.",
            "Simulate or observe reportSetup update API failure on Generate.",
            "Confirm error message and that COMMAND is not started.",
        ],
        "expected_results": [
            "Selection changes are made.",
            "Error toast Failed to update ASCII channel selection is shown.",
            "COMMAND GenerateASCII is not invoked.",
        ],
    },
    {
        "title": "Verify COMMAND failure shows generation error after configuration path completes",
        "steps": [
            "Trigger Generate with valid/unchanged or successfully saved configuration.",
            "Simulate or observe COMMAND/SignalR GenerateASCII failure.",
            "Confirm error feedback to the user.",
        ],
        "expected_results": [
            "Generate path reaches COMMAND.",
            "COMMAND/SignalR returns error for GenerateASCII.",
            "Error toast indicates report generation was unsuccessful and ASCII button recovers.",
        ],
    },
    # Scenario 5 — cancel
    {
        "title": "Verify Cancel closes dialog without reportSetup update or COMMAND",
        "steps": [
            "Open ASCII Report dialog.",
            "Optionally change channel selections then click Cancel.",
            "Monitor network for reportSetup update and COMMAND calls.",
        ],
        "expected_results": [
            "Dialog is open.",
            "Cancel closes the dialog.",
            "No reportSetup update and no COMMAND GenerateASCII are invoked.",
        ],
    },
    {
        "title": "Verify Cancel discards unsaved channel selection changes on next open",
        "steps": [
            "Open ASCII dialog and change Real-time/FracPro selections.",
            "Click Cancel.",
            "Reopen ASCII dialog and inspect selections.",
        ],
        "expected_results": [
            "Unsaved selection changes were made.",
            "Dialog closes on Cancel.",
            "Reopened dialog shows previously saved selections only.",
        ],
    },
    {
        "title": "Verify close X dismisses dialog without saving channel configuration",
        "steps": [
            "Open ASCII dialog and change selections.",
            "Click the header close X control.",
            "Confirm dialog closes without reportSetup update or COMMAND.",
        ],
        "expected_results": [
            "Selections were changed.",
            "X closes the dialog.",
            "No save and no COMMAND occur.",
        ],
    },
    # Supporting UI for this US
    {
        "title": "Verify Real-time and FracPro tabs are available for channel configuration in ASCII dialog",
        "steps": [
            "Open the ASCII Report dialog.",
            "Inspect available tabs.",
            "Switch between Real-time and FracPro tabs.",
        ],
        "expected_results": [
            "Dialog opens.",
            "Real-time and FracPro tabs are visible.",
            "Each tab shows its channel selection grid.",
        ],
    },
    {
        "title": "Verify Generate and Cancel actions are available to complete ASCII configuration flow",
        "steps": [
            "Open the ASCII Report dialog.",
            "Locate footer action buttons.",
            "Confirm Generate and Cancel are present and enabled after load.",
        ],
        "expected_results": [
            "Dialog opens.",
            "Generate and Cancel buttons are visible.",
            "After loading completes, Generate and Cancel are usable.",
        ],
    },
    {
        "title": "Verify clicking ASCII Report opens configuration dialog before any COMMAND call",
        "steps": [
            "On Reports click ASCII Report.",
            "Monitor network for COMMAND on the click.",
            "Confirm configuration dialog opens first.",
        ],
        "expected_results": [
            "ASCII Report button is clicked.",
            "No COMMAND call occurs on open alone.",
            "ASCII configuration dialog is shown.",
        ],
    },
    {
        "title": "Verify select-all Real-time change is persisted to asciirealtime on Generate",
        "steps": [
            "Open ASCII dialog on Real-time tab.",
            "Use select-all to change Real-time selections, then Generate.",
            "Confirm reportSetup update contains the select-all result for asciirealtime.",
        ],
        "expected_results": [
            "Real-time channels are listed.",
            "Select-all changes selection state.",
            "Updated asciirealtime is saved then COMMAND runs.",
        ],
    },
    {
        "title": "Verify clearing all FracPro selections persists cleared asciifp on Generate",
        "steps": [
            "Open ASCII dialog with some FracPro channels previously selected.",
            "Clear all FracPro selections and click Generate.",
            "Inspect reportSetup update asciifp value.",
        ],
        "expected_results": [
            "Prior FracPro selections existed.",
            "All FracPro selections are cleared.",
            "asciifp is saved as empty list then COMMAND runs.",
        ],
    },
    # Regression
    {
        "title": "Verify Word Report generation still works after ASCII Generate with config save",
        "steps": [
            "Complete an ASCII Generate that updates channel configuration.",
            "Click Download Word Report.",
            "Confirm Word report generation still initiates.",
        ],
        "expected_results": [
            "ASCII generate with save completes.",
            "Word Report button remains usable.",
            "Word report COMMAND/download flow still works.",
        ],
    },
    {
        "title": "Verify WITSML download still initiates after ASCII saved-channel Generate completes",
        "steps": [
            "Complete ASCII Generate using saved or updated channel configuration.",
            "Click Download WITSML Report.",
            "Confirm WITSML flow still starts.",
        ],
        "expected_results": [
            "ASCII flow completes.",
            "WITSML button is clickable.",
            "WITSML generation/download still works.",
        ],
    },
    {
        "title": "Verify Reports Save still works after Cancel of ASCII configuration dialog",
        "steps": [
            "Open ASCII dialog, change selections, Cancel.",
            "Click Save on Reports.",
            "Confirm Save still functions.",
        ],
        "expected_results": [
            "ASCII dialog cancelled without save.",
            "Save button is available.",
            "Reports Save still works without regression.",
        ],
    },
    {
        "title": "Verify ASCII generation uses current Reports wellId and treatmentId",
        "steps": [
            "Note current wellId and treatmentId on Reports.",
            "Open ASCII dialog and Generate.",
            "Confirm COMMAND payload uses those well and treatment ids.",
        ],
        "expected_results": [
            "Current well/treatment context is known.",
            "Generate runs.",
            "GenerateASCII COMMAND uses the current Reports wellId and treatmentId.",
        ],
    },
    {
        "title": "Verify Generate with both Real-time and FracPro changes updates asciirealtime and asciifp together",
        "steps": [
            "Open ASCII Report dialog and change selections on Real-time and FracPro tabs.",
            "Click Generate.",
            "Inspect reportSetup update payload and subsequent COMMAND.",
        ],
        "expected_results": [
            "Both Real-time and FracPro selections differ from saved values.",
            "Single reportSetup update includes both asciirealtime and asciifp.",
            "After successful update, COMMAND GenerateASCII runs once.",
        ],
    },
    {
        "title": "Verify Generate is disabled while ASCII channel lists are still loading",
        "steps": [
            "Open the ASCII Report dialog.",
            "While loading skeleton is visible, attempt to click Generate.",
            "Wait for load to finish and confirm Generate becomes enabled.",
        ],
        "expected_results": [
            "Dialog opens in loading state.",
            "Generate remains disabled while isLoading is true.",
            "After channels and reportSetup load, Generate is enabled for use.",
        ],
    },
]

# 27 cases → Critical 3, Regression 9
CRITICAL = [3, 4, 5]
REGRESSION = [16, 17, 18, 19, 22, 23, 24, 25, 27]


def write_artifacts() -> list[dict]:
    n = len(CASES)
    for i, c in enumerate(CASES, 1):
        if len(c["steps"]) != len(c["expected_results"]):
            raise SystemExit(f"parity fail TC-{i}")

    reg_n = int(n * 0.30 + 0.5)
    crit_n = int(n * 0.10 + 0.5)
    critical = [i for i in CRITICAL if i <= n][:crit_n]
    regression = [i for i in REGRESSION if i <= n and i not in critical][:reg_n]
    labels = {
        i: "Critical" if i in critical else "Regression" if i in regression else "Standard"
        for i in range(1, n + 1)
    }
    enriched = [{**c, "label": labels[i]} for i, c in enumerate(CASES, 1)]

    gaps = [
        "IMPLEMENTED: loadReportSetup via GET .../reportSetup (getAvailablePlots); defaults for empty asciirealtime/asciifp.",
        "IMPLEMENTED: onGenerate compares selections; updateReportSetup when changed; skip update when unchanged; then COMMAND.",
        "IMPLEMENTED: PUT path is actually POST /v1/Wells/{wellId}/reportSetup — preserves other reportSetup fields via spread.",
        "IMPLEMENTED: Cancel/X emit cancelled without update/COMMAND; PUT failure toast blocks COMMAND; COMMAND errors via handleError.",
        "GAP-1 (HTTP method): AC says PUT reportSetup; code uses POST updateReportSetup — confirm with API contract/BA.",
        "GAP-2 (Wording): AC uses FrPro; UI tab label is FracPro.",
        "GAP-3 (Cancel during save): Cancel/X disabled while isGenerating during updateReportSetup.",
        "GAP-4 (GET naming): AC says GET reportSetup; client method is getAvailablePlots() hitting same reportSetup endpoint.",
        "Rule 12: auto feature_found=false on broad scan, but related ASCII dialog/generate flow is clearly present — generating from related implementation.",
    ]

    md = [
        f"STORY: {STORY}",
        f"US: {US}",
        f"COUNT: {n}",
        "NOTE: Dry-run drafts — not uploaded to ADO",
        f"CODEBASE: {CODEBASE}",
        "STATE: QA | Existing linked TCs: 0 | Fresh suite",
        "SCOPE: US-116561 saved channel configuration generate flow (5 AC scenarios)",
        f"RULE 13 MIX: Critical {crit_n} / Regression {reg_n}",
        "",
        "## Gaps (US vs QA codebase)",
    ]
    md.extend(f"- {g}" for g in gaps)
    md.extend(["", "## Label summary", "", f"### Critical / Sanity ({crit_n})"])
    md.extend(f"- TC-{i}: {CASES[i - 1]['title']}" for i in critical)
    md.extend(["", f"### Regression ({reg_n})"])
    md.extend(f"- TC-{i}: {CASES[i - 1]['title']}" for i in regression)
    md.extend(["", "### Standard"])
    md.extend(
        f"- TC-{i}: {CASES[i - 1]['title']}"
        for i in range(1, n + 1)
        if labels[i] == "Standard"
    )
    md.extend(["", "---", ""])
    for i, c in enumerate(CASES, 1):
        md.append(f"### TC-{i}: {c['title']}")
        md.append(f"**Label:** {labels[i]}")
        md.append("**Steps**")
        md.extend(f"{j}. {s}" for j, s in enumerate(c["steps"], 1))
        md.append("**Expected Results**")
        md.extend(f"{j}. {e}" for j, e in enumerate(c["expected_results"], 1))
        md.append("")

    Path(f"tmp_drafts_{US}_curated_qa.md").write_text("\n".join(md), encoding="utf-8")
    Path(f"tmp_drafts_{US}_curated_qa.json").write_text(
        json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    Path(f"tmp_out_{US}_gaps.json").write_text(
        json.dumps(
            {
                "gaps": gaps,
                "codebase": CODEBASE,
                "existing_linked_tcs": 0,
                "draft_count": n,
                "feature_related": True,
                "http": {
                    "get": "GET .../Wells/{wellId}/reportSetup via getAvailablePlots",
                    "update": "POST .../Wells/{wellId}/reportSetup via updateReportSetup (AC says PUT)",
                    "command": "SignalR GenerateASCII via startAsciiCommand/handleSignalR",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote n={n} critical={critical} regression={regression}")
    return enriched


async def dry_run(enriched: list[dict]) -> None:
    payload = [
        {"title": c["title"], "steps": c["steps"], "expected_results": c["expected_results"]}
        for c in enriched
    ]
    result = await create_test_cases(test_cases=payload, dry_run=True, user_story_id=US)
    data = result.get("data") or []
    print(
        "dry_run",
        result.get("ok"),
        Counter(x.get("status") for x in data) if isinstance(data, list) else result.get("error"),
    )
    Path(f"tmp_out_{US}_dry_run_qa.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8"
    )


if __name__ == "__main__":
    enriched = write_artifacts()
    asyncio.run(dry_run(enriched))
