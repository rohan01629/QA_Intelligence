"""Build curated TC suite for US 115589 with Rule 13 labels."""
from __future__ import annotations

import asyncio
import json
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from qa_intelligence.mcp.tools.create_test_cases import create_test_cases

US = 115589
STORY = (
    "FracPro Live+ Plots - Prepopulate Current Template Name "
    "in the Save Template Dialog for Existing Templates"
)

# 50 atomic cases — title / steps / expected_results only in ADO payload
CASES: list[dict] = [
    {
        "title": "Verify Save Template dialog prepopulates current name for an existing opened template",
        "steps": [
            "Open Plots and load an existing named plot template (not a new untitled template).",
            "Click the Save Template / Save Plot button.",
            "Inspect the Template Name / Plot Name field in the dialog.",
        ],
        "expected_results": [
            "Existing template is active and its name is visible in the Plots header.",
            "Save Template dialog opens.",
            "Template Name field is automatically populated with the current template name.",
        ],
    },
    {
        "title": "Verify prepopulated name matches the template shown in the Plots header",
        "steps": [
            "Open an existing template whose name is displayed in the Plots title area.",
            "Open Save Template.",
            "Compare the dialog name field to the header template name.",
        ],
        "expected_results": [
            "Header shows the current template name.",
            "Dialog opens successfully.",
            "Dialog name field equals the header template name exactly.",
        ],
    },
    {
        "title": "Verify Save without changing the prepopulated name saves the existing template successfully",
        "steps": [
            "Open an existing template and open Save Template so the current name is prepopulated.",
            "Do not edit the name field; click Save.",
            "Confirm the template list/header after save completes.",
        ],
        "expected_results": [
            "Dialog shows the current template name.",
            "Save completes without requiring a name re-entry.",
            "Existing template is saved successfully and remains the active template under the same name.",
        ],
    },
    {
        "title": "Verify Save without name change updates template content/configuration for the same template id",
        "steps": [
            "Open an existing template, make an allowed plot configuration change, then open Save Template.",
            "Leave the prepopulated name unchanged and click Save.",
            "Re-open or reload the same template and inspect the saved configuration.",
        ],
        "expected_results": [
            "Dialog name matches the existing template.",
            "Save succeeds for that template.",
            "Saved configuration reflects the change under the same template identity/name.",
        ],
    },
    {
        "title": "Verify editing the prepopulated name and saving applies the updated template name",
        "steps": [
            "Open an existing template and open Save Template with the current name prepopulated.",
            "Change the name to a new valid unique name and click Save.",
            "Observe the saved template name in the UI/list.",
        ],
        "expected_results": [
            "Dialog opens with the original name prepopulated.",
            "Edited name is accepted by the dialog.",
            "Template is saved using the updated name.",
        ],
    },
    {
        "title": "Verify Save with updated name still applies existing template name validation rules",
        "steps": [
            "Open Save Template for an existing template with name prepopulated.",
            "Change the name to a value that violates an existing validation rule (e.g. empty or restricted name).",
            "Attempt to Save and observe validation/error behavior.",
        ],
        "expected_results": [
            "Dialog shows the current name initially.",
            "Invalid edited name is entered.",
            "Existing template name validation rules prevent a successful invalid save (error/disabled Save as designed).",
        ],
    },
    {
        "title": "Verify New Template Save dialog leaves Template Name blank",
        "steps": [
            "Start creating a new template / untitled plot context (no existing named template loaded).",
            "Open the Save Template dialog.",
            "Inspect the Template Name field.",
        ],
        "expected_results": [
            "New-template context is active.",
            "Save Template dialog opens.",
            "Template Name field remains blank (current new-template behavior).",
        ],
    },
    {
        "title": "Verify New Template blank name is not prefilled from a previously opened existing template",
        "steps": [
            "Open an existing named template, then navigate to a new/untitled template context.",
            "Open Save Template.",
            "Inspect the name field.",
        ],
        "expected_results": [
            "New/untitled context is active.",
            "Dialog opens.",
            "Name field is blank and does not retain the previous existing template name.",
        ],
    },
    {
        "title": "Verify Save Template prepopulation works for a user-defined (type 2) existing template",
        "steps": [
            "Open an existing user-defined plot template.",
            "Click Save Template.",
            "Check the name field value.",
        ],
        "expected_results": [
            "User-defined template loads.",
            "Dialog opens.",
            "Name field is prepopulated with that user-defined template name.",
        ],
    },
    {
        "title": "Verify Save Template prepopulation works for a Pad/company (type 3) existing template when Save is available",
        "steps": [
            "Open an existing Pad/company plot template where Save Template is enabled.",
            "Open Save Template.",
            "Inspect the name field and pad-related checkbox state if shown.",
        ],
        "expected_results": [
            "Pad template context loads and Save is available.",
            "Dialog opens.",
            "Name field is prepopulated with the current Pad template name.",
        ],
    },
    {
        "title": "Verify clearing the prepopulated name prevents empty-name save",
        "steps": [
            "Open Save Template for an existing template with name prepopulated.",
            "Clear the name field completely.",
            "Attempt to Save.",
        ],
        "expected_results": [
            "Name was prepopulated.",
            "Name field is empty.",
            "Save is blocked or fails validation; empty plot/template name is not accepted.",
        ],
    },
    {
        "title": "Verify restricted name 'surf prc' is rejected when editing from a prepopulated existing name",
        "steps": [
            "Open Save Template for an existing template.",
            "Replace the prepopulated name with 'surf prc' and click Save.",
            "Observe error/toast messaging.",
        ],
        "expected_results": [
            "Dialog opened with original name.",
            "Restricted name is entered.",
            "Save is rejected with the existing restricted-name error behavior.",
        ],
    },
    {
        "title": "Verify restricted name 'btm prc' is rejected on Save Template",
        "steps": [
            "Open Save Template for an existing template.",
            "Change the name to 'btm prc' and attempt Save.",
            "Observe validation/error handling.",
        ],
        "expected_results": [
            "Dialog is open.",
            "Restricted name is submitted.",
            "Save is rejected per existing restricted-name rules.",
        ],
    },
    {
        "title": "Verify restricted name 'measured data' is rejected on Save Template",
        "steps": [
            "Open Save Template for an existing template.",
            "Change the name to 'measured data' and attempt Save.",
            "Observe validation/error handling.",
        ],
        "expected_results": [
            "Dialog is open.",
            "Restricted name is submitted.",
            "Save is rejected per existing restricted-name rules.",
        ],
    },
    {
        "title": "Verify duplicate template name conflict still surfaces when renaming via Save Template",
        "steps": [
            "Open existing template A and open Save Template (name A prepopulated).",
            "Change the name to an existing different template B name and attempt Save.",
            "Observe conflict messaging and whether Save is blocked.",
        ],
        "expected_results": [
            "Dialog shows A initially.",
            "Name is changed to B.",
            "Existing name-conflict validation prevents an invalid overwrite/conflict save as designed.",
        ],
    },
    {
        "title": "Verify plot name max length (50) validation still applies with prepopulated names",
        "steps": [
            "Open Save Template for an existing template.",
            "Edit the name to exceed the 50-character limit (or paste beyond max).",
            "Attempt Save / observe inline limit feedback.",
        ],
        "expected_results": [
            "Dialog opens with current name.",
            "Over-limit input is attempted.",
            "Existing max-length validation/limit feedback prevents invalid save.",
        ],
    },
    {
        "title": "Verify Cancel/close on Save Template does not change the loaded template name",
        "steps": [
            "Open an existing template and open Save Template with prepopulated name.",
            "Optionally edit the name, then Cancel/close the dialog without Save.",
            "Confirm the active template name in Plots.",
        ],
        "expected_results": [
            "Dialog shows prepopulated name.",
            "Dialog is dismissed without Save.",
            "Active template name/content remains unchanged.",
        ],
    },
    {
        "title": "Verify reopening Save Template after Cancel still prepopulates the current existing name",
        "steps": [
            "Open Save Template for an existing template, Cancel without saving.",
            "Open Save Template again.",
            "Inspect the name field.",
        ],
        "expected_results": [
            "First dialog is cancelled.",
            "Second dialog opens.",
            "Name field is again prepopulated with the current existing template name.",
        ],
    },
    {
        "title": "Verify switching from template A to template B updates the prepopulated Save name",
        "steps": [
            "Open existing template A, open Save Template, note prepopulated name A, then close.",
            "Switch to existing template B and open Save Template.",
            "Inspect the name field.",
        ],
        "expected_results": [
            "A was prepopulated correctly on first open.",
            "B becomes the active template.",
            "Dialog for B shows B’s name (not stale A).",
        ],
    },
    {
        "title": "Verify whitespace-only name is not accepted when replacing a prepopulated name",
        "steps": [
            "Open Save Template for an existing template.",
            "Replace the name with spaces only and attempt Save.",
            "Observe validation.",
        ],
        "expected_results": [
            "Dialog opens.",
            "Whitespace-only name is entered.",
            "Save is blocked by existing non-empty name validation.",
        ],
    },
    {
        "title": "Verify Save button remains usable when prepopulated name is left unchanged (dirty/valid path)",
        "steps": [
            "Open Save Template for an existing template with name prepopulated.",
            "Without editing, evaluate whether Save can proceed for an unchanged existing name (per product rules).",
            "Click Save if enabled, or document required minimal interaction if product requires dirty state.",
        ],
        "expected_results": [
            "Name is prepopulated.",
            "Save affordance is evaluated for unchanged-name path.",
            "User can complete Scenario 2 save-without-changing-name successfully (or documented UX step if dirty flag is required).",
        ],
    },
    {
        "title": "Verify UpdatePlotTemplate path is used when saving existing template with same name",
        "steps": [
            "Open an existing template and open Save Template with matching current name.",
            "Save without changing the name while monitoring network/API (Update vs create).",
            "Confirm the same template is updated rather than a brand-new duplicate create when names match.",
        ],
        "expected_results": [
            "Existing template context is active.",
            "Save is submitted with the same name.",
            "Update existing template path is used (no unintended duplicate template with same name).",
        ],
    },
    {
        "title": "Verify create/savePlotTemplate path is used when saving a new template with a blank-started name filled in",
        "steps": [
            "Open Save Template in new-template context (blank name).",
            "Enter a unique valid name and Save.",
            "Observe that a new template is created and appears in the list.",
        ],
        "expected_results": [
            "Name starts blank.",
            "Valid unique name is saved.",
            "New template is created successfully.",
        ],
    },
    {
        "title": "Verify UI: Save Template dialog title and name label remain clear when name is prepopulated",
        "steps": [
            "Open Save Template for an existing template.",
            "Observe dialog title and the name input label/value.",
            "Confirm the prepopulated value is fully visible/editable.",
        ],
        "expected_results": [
            "Dialog opens.",
            "Title/label are readable.",
            "Prepopulated name is visible and editable without layout clipping.",
        ],
    },
    {
        "title": "Verify UI: long existing template names display and remain editable in the Save dialog",
        "steps": [
            "Open an existing template with a long valid name (near max length).",
            "Open Save Template.",
            "Confirm the full name is present in the field and can be edited.",
        ],
        "expected_results": [
            "Long-named template is open.",
            "Dialog opens.",
            "Name field contains the long current name and remains editable.",
        ],
    },
    {
        "title": "Verify special characters allowed by current rules still save when editing a prepopulated name",
        "steps": [
            "Open Save Template for an existing template.",
            "Edit the name to include special characters that are currently allowed by product rules.",
            "Save and confirm the new name persists.",
        ],
        "expected_results": [
            "Dialog opens with original name.",
            "Allowed special-character name is entered.",
            "Save succeeds and the updated name is shown.",
        ],
    },
    {
        "title": "Verify case differences follow existing conflict/validation rules when saving from prepopulated name",
        "steps": [
            "Open Save Template for existing template named in mixed case.",
            "Change only letter casing if product treats names case-insensitively for conflicts, or keep case if uniqueness is case-sensitive.",
            "Save and observe conflict vs success per existing rules.",
        ],
        "expected_results": [
            "Dialog shows original name.",
            "Casing-only edit is attempted.",
            "Behavior matches existing case-insensitive/case-sensitive template name rules.",
        ],
    },
    {
        "title": "Verify Save Template while chart data is loading does not corrupt the prepopulated name",
        "steps": [
            "Open an existing template; if loading indicators appear, open Save Template when the button is enabled.",
            "Inspect the prepopulated name.",
            "Cancel or Save only if stable.",
        ],
        "expected_results": [
            "Existing template context is known.",
            "Dialog opens when Save is available.",
            "Name field shows the correct current template name (not blank/garbage).",
        ],
    },
    {
        "title": "Verify disabled Save Template states for invalid template contexts still apply",
        "steps": [
            "Navigate to a plot context where Save is disabled (e.g. missing name/id or restricted system plot if applicable).",
            "Confirm Save Template cannot be opened incorrectly.",
            "Switch to a valid existing named template and confirm Save becomes available.",
        ],
        "expected_results": [
            "Invalid context disables Save as before.",
            "User cannot open an invalid Save path from that disabled state.",
            "Valid existing template re-enables Save and prepopulates correctly.",
        ],
    },
    {
        "title": "Verify after saving with updated name, subsequent Save Template prepopulates the new name",
        "steps": [
            "From an existing template, Save Template with an updated valid name successfully.",
            "Open Save Template again on the now-current template.",
            "Inspect the name field.",
        ],
        "expected_results": [
            "First save with new name succeeds.",
            "Dialog opens again.",
            "Name field is prepopulated with the newly saved name.",
        ],
    },
    {
        "title": "Verify Save without changing name does not create a second list entry with the same name",
        "steps": [
            "Note the template list count/names for an existing template.",
            "Open Save Template, leave name unchanged, Save.",
            "Refresh/observe the template list.",
        ],
        "expected_results": [
            "Baseline list is known.",
            "Same-name save succeeds.",
            "No duplicate list entry is created for the same template name/id.",
        ],
    },
    {
        "title": "Verify edge: template name with leading/trailing spaces is trimmed per existing save logic",
        "steps": [
            "Open Save Template for an existing template.",
            "Edit the name to include leading/trailing spaces around a valid unique name and Save.",
            "Inspect the stored/displayed name.",
        ],
        "expected_results": [
            "Dialog opens.",
            "Spaced name is submitted.",
            "Saved name follows existing trim behavior (spaces not unexpectedly preserved if product trims).",
        ],
    },
    {
        "title": "Verify edge: rapid open/close of Save Template keeps prepopulation correct",
        "steps": [
            "On an existing template, open and close Save Template several times quickly.",
            "Open it once more and leave it open.",
            "Inspect the name field.",
        ],
        "expected_results": [
            "Multiple open/close cycles complete.",
            "Final dialog is open.",
            "Name remains correctly prepopulated with the current template name.",
        ],
    },
    {
        "title": "Verify edge: Save Template after switching wells still uses the active well’s current template name",
        "steps": [
            "On well A open an existing template and confirm Save prepopulation.",
            "Switch to well B, open an existing template there, open Save Template.",
            "Confirm the prepopulated name belongs to well B’s active template.",
        ],
        "expected_results": [
            "Well A path works.",
            "Well B template is active.",
            "Dialog shows well B’s current template name (not well A stale name).",
        ],
    },
    {
        "title": "Verify negative: Save Template API/update failure shows error and leaves UI recoverable",
        "steps": [
            "Open Save Template for an existing template with a valid prepopulated/edited name.",
            "Cause or observe a save/update API failure.",
            "Check error feedback and that the dialog/Plots UI remains usable.",
        ],
        "expected_results": [
            "Save is attempted.",
            "Failure is surfaced (toast/log/error per product).",
            "UI remains recoverable; user can retry or cancel.",
        ],
    },
    {
        "title": "Verify negative: opening Save Template does not mutate template content before Save",
        "steps": [
            "Note current plot configuration for an existing template.",
            "Open Save Template (name prepopulated) and Cancel.",
            "Confirm plot configuration is unchanged.",
        ],
        "expected_results": [
            "Baseline configuration is known.",
            "Dialog is cancelled.",
            "No unintended content mutation occurred from merely opening the dialog.",
        ],
    },
    {
        "title": "Verify Rename Plot still prepopulates current name (neighbor workflow unchanged)",
        "steps": [
            "Open an existing template.",
            "Use Rename Plot (not Save Template).",
            "Confirm the rename dialog name field is prepopulated.",
        ],
        "expected_results": [
            "Existing template is active.",
            "Rename dialog opens.",
            "Rename still prepopulates the current name as before.",
        ],
    },
    {
        "title": "Verify Duplicate Plot still opens with expected name handling",
        "steps": [
            "Open an existing saved template.",
            "Use Duplicate Plot.",
            "Confirm duplicate dialog behavior for name/content still works.",
        ],
        "expected_results": [
            "Template is eligible for duplicate.",
            "Duplicate dialog opens.",
            "Duplicate workflow remains functional (no regression from Save Template prepopulate change).",
        ],
    },
    {
        "title": "Verify Delete Plot confirmation still shows the correct current template name",
        "steps": [
            "Open an existing named template.",
            "Initiate Delete Plot.",
            "Confirm the confirmation UI references the correct template name.",
        ],
        "expected_results": [
            "Template is open.",
            "Delete confirmation appears.",
            "Displayed name matches the current template (neighbor delete workflow intact).",
        ],
    },
    {
        "title": "Verify loading another template from the sidebar still works after using Save Template",
        "steps": [
            "Save an existing template via Save Template (same or updated name).",
            "Select a different template from the Plots sidebar/list.",
            "Confirm the other template loads.",
        ],
        "expected_results": [
            "Save completes.",
            "Different template is selected.",
            "Other template loads correctly (no list/navigation regression).",
        ],
    },
    {
        "title": "Verify graph-config / channel settings workflows still open after Save Template changes",
        "steps": [
            "Open an existing template and optionally use Save Template once.",
            "Open channel/settings related plot configuration UI used on Plots.",
            "Confirm those dialogs still open and function.",
        ],
        "expected_results": [
            "Template context is available.",
            "Settings/channel UI opens.",
            "Neighbor plot configuration workflows remain usable.",
        ],
    },
    {
        "title": "Verify Export/print or other plot toolbar actions still work after Save Template prepopulate change",
        "steps": [
            "Open an existing template.",
            "Exercise a previously working toolbar action (export/print/download if available).",
            "Open Save Template and confirm name prepopulation still works afterward.",
        ],
        "expected_results": [
            "Template is open.",
            "Toolbar action still works.",
            "Save Template still prepopulates correctly.",
        ],
    },
    {
        "title": "Verify Word/report neighbor plot save flows remain unaffected",
        "steps": [
            "From Reports/related plot save areas if accessible in the same build, exercise an existing save flow unrelated to Plots Save Template prepopulate.",
            "Return to Plots Save Template for an existing template.",
            "Confirm Plots prepopulation still works.",
        ],
        "expected_results": [
            "Neighbor report/save path remains usable or N/A is documented if out of scope for environment.",
            "User returns to Plots.",
            "Plots Save Template prepopulation still works for existing templates.",
        ],
    },
    {
        "title": "Verify current build gap: Save Plot openFormModal does not yet patch current template name",
        "steps": [
            "In Live_Plus_UAT, open an existing named template.",
            "Click Save Plot and inspect whether plotName is blank vs prepopulated.",
            "Compare to Rename Plot which already calls prepareRenamePlotModal with currentName.",
        ],
        "expected_results": [
            "Existing template is open.",
            "Save Plot currently opens via openFormModal without preparing the current name (gap vs US 115589).",
            "Rename path still demonstrates prepopulation pattern via prepareRenamePlotModal.",
        ],
    },
    {
        "title": "Verify after implementation: first Save Template on existing template shows name without manual typing",
        "steps": [
            "After the story is implemented, open an existing template.",
            "Open Save Template once.",
            "Confirm the name field is filled before any typing.",
        ],
        "expected_results": [
            "Feature is available.",
            "Dialog opens.",
            "Current template name is present with zero typing (Scenario 1).",
        ],
    },
    {
        "title": "Verify after implementation: unchanged-name Save completes Scenario 2",
        "steps": [
            "After implementation, open Save Template on an existing template.",
            "Click Save without editing the name.",
            "Confirm successful save of the existing template.",
        ],
        "expected_results": [
            "Name is prepopulated.",
            "Save is clicked unchanged.",
            "Existing template saves successfully.",
        ],
    },
    {
        "title": "Verify after implementation: renamed Save completes Scenario 3 with validations",
        "steps": [
            "After implementation, open Save Template on an existing template.",
            "Change to a valid unique name and Save; also spot-check one invalid name is still blocked.",
            "Confirm updated name save and validation still apply.",
        ],
        "expected_results": [
            "Dialog prepopulates.",
            "Valid rename save succeeds.",
            "Invalid names still fail existing validation rules.",
        ],
    },
    {
        "title": "Verify after implementation: new template Save dialog name stays blank (Scenario 4)",
        "steps": [
            "After implementation, open Save Template in new-template context.",
            "Inspect the name field.",
            "Optionally enter a name and save a new template.",
        ],
        "expected_results": [
            "New-template context is active.",
            "Name field is blank on open.",
            "New template can still be saved after entering a name.",
        ],
    },
    {
        "title": "Verify after implementation: Save Template prepopulation parity with Rename for the same existing template",
        "steps": [
            "After implementation, open the same existing template.",
            "Open Rename and note the prepopulated name; close.",
            "Open Save Template and compare the prepopulated name.",
        ],
        "expected_results": [
            "Same template is active for both dialogs.",
            "Rename shows current name.",
            "Save Template shows the same current name.",
        ],
    },
    {
        "title": "Verify after implementation: end-to-end existing template open → Save Template → save → list/header stay consistent",
        "steps": [
            "After implementation, open existing template T, open Save Template, save with same or updated valid name.",
            "Observe header name and sidebar list entry.",
            "Re-open Save Template once more.",
        ],
        "expected_results": [
            "Save completes.",
            "Header and list show the saved name consistently.",
            "Subsequent Save Template prepopulates that saved name.",
        ],
    },
]

# Rule 13 — Critical first (10%=5), then Regression (30%=15), by business impact
CRITICAL = [1, 3, 5, 7, 6]  # Scenarios 1,2,3,4 + validation on rename path
# Fix order for readability in summary:
CRITICAL = [1, 3, 5, 6, 7]
REGRESSION = [37, 38, 39, 40, 41, 42, 43, 17, 18, 19, 29, 30, 31, 9, 10]


def write_artifacts() -> list[dict]:
    n = len(CASES)
    assert n == 50, n
    reg_n = int(n * 0.30 + 0.5)
    crit_n = int(n * 0.10 + 0.5)
    assert len(CRITICAL) == crit_n and len(REGRESSION) == reg_n
    assert not (set(CRITICAL) & set(REGRESSION))

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
    enriched = [{**c, "label": labels[i]} for i, c in enumerate(CASES, 1)]

    Path(f"tmp_drafts_{US}_curated.json").write_text(
        json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    Path(f"tmp_out_{US}_labels.json").write_text(
        json.dumps(
            {
                "user_story_id": US,
                "total": n,
                "targets": {
                    "critical": crit_n,
                    "regression": reg_n,
                    "standard": n - crit_n - reg_n,
                },
                "critical_tc_numbers": CRITICAL,
                "regression_tc_numbers": REGRESSION,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    md: list[str] = [
        f"STORY: {STORY}",
        f"US: {US}",
        f"COUNT: {n}",
        "NOTE: Dry-run curated drafts — not uploaded to ADO",
        r"SOURCE: AC (4 Scenario blocks) + D:\Live_Plus_UAT plots-option + reuseable-modal "
        "(Save Plot openFormModal currently does not patch plotName; Rename uses prepareRenamePlotModal). "
        "Minifrac tree not primary for this Plots story.",
        "COMPLEXITY: complex (4 Scenario N → Rule 11 ~50)",
        "CODEBASES_ANALYZED:",
        r"  - D:\Live_Plus_UAT (primary)",
        r"  - C:\Users\WalkingTree.LAPTOP-UNM23JON\Desktop\Minifrac\fracpro-agile (secondary scan)",
        "RULE 13 MIX: Critical 10% / Regression 30%",
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
        md.append(f"- TC-{i}: {CASES[i - 1]['title']}")
    md.append("")
    md.append(f"### Regression (30% = {reg_n})")
    for i in REGRESSION:
        md.append(f"- TC-{i}: {CASES[i - 1]['title']}")
    md.append("")
    md.append(f"### Standard (60% = {n - crit_n - reg_n})")
    for i in range(1, n + 1):
        if labels[i] == "Standard":
            md.append(f"- TC-{i}: {CASES[i - 1]['title']}")
    md.extend(["", "---", ""])

    for i, c in enumerate(CASES, 1):
        md.append(f"### TC-{i}: {c['title']}")
        md.append(f"**Label:** {labels[i]}")
        md.append("**Steps**")
        for j, s in enumerate(c["steps"], 1):
            md.append(f"{j}. {s}")
        md.append("**Expected Results**")
        for j, e in enumerate(c["expected_results"], 1):
            md.append(f"{j}. {e}")
        md.append("")

    Path(f"tmp_drafts_{US}_curated.md").write_text("\n".join(md), encoding="utf-8")
    print(f"wrote drafts n={n} critical={CRITICAL} regression={REGRESSION}")
    return enriched


async def dry_run(enriched: list[dict]) -> None:
    payload = [
        {
            "title": c["title"],
            "steps": c["steps"],
            "expected_results": c["expected_results"],
        }
        for c in enriched
    ]
    for i, c in enumerate(payload, 1):
        if len(c["steps"]) != len(c["expected_results"]):
            raise SystemExit(f"parity fail TC-{i}")
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
    Path(f"tmp_out_{US}_dry_run.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8"
    )


if __name__ == "__main__":
    enriched = write_artifacts()
    asyncio.run(dry_run(enriched))
