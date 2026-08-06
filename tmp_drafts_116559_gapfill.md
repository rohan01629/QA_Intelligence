STORY: FracPro Live+ - Reports- Rename Download ASCII Report button and launch ASCII Report dialog
US: 116559
MODE: Gap-fill only (Rule 3) — existing linked TCs: 22
COUNT: 3 (missing only)
NOTE: Dry-run drafts — not uploaded to ADO
CODEBASE: D:\Live_Plus_QA\fracpro-agile (branch wtt/liveplus/qa-rohan)
STATE: QA Complete | Feature found (onOpenAsciiReportDialog + ASCII Report label)
RULE 13: All 3 planned as Regression (adjacent Reports controls)

## Inventory summary
Existing linked coverage already includes rename, open-dialog-without-COMMAND, tabs, Generate/Cancel/X, channel grids, select-all, Operator deny, defaults, loading skeleton, failed updateReportSetup, and Save regression.

## Gaps vs curated suite / code
- MISSING: Word Report download still works after ASCII dialog cancel
- MISSING: WITSML download still works after ASCII dialog flow
- MISSING: Material Usage Import from XOPS still present/usable after ASCII dialog
- NOTE: AC says tabs Real-time / FracPro on all three Reports tabs (Word, Material Usage, Post Job Data) — button presence already covered by existing TCs 117336–117338

## Label summary

### Regression (3)
- Verify Download Word Report still works after ASCII dialog cancel
- Verify Download WITSML Report still works after ASCII dialog flow
- Verify Import from XOPS remains available on Material Usage after ASCII dialog

---

### Verify Download Word Report still works after ASCII dialog cancel
**Label:** Regression
**is_regression:** true
**is_sanity:** false
**Steps**
1. Open Reports on the Word Report tab.
2. Click ASCII Report, then Cancel (or close X) without Generate.
3. Click Download Word Report and observe generation/download behavior.
**Expected Results**
1. Word Report tab is active with report action buttons visible.
2. ASCII dialog opens and dismisses without starting GenerateASCII COMMAND.
3. Word Report download still initiates successfully with no regression from the ASCII dialog path.

### Verify Download WITSML Report still works after ASCII dialog flow
**Label:** Regression
**is_regression:** true
**is_sanity:** false
**Steps**
1. Open Reports on any tab that shows Download WITSML Report.
2. Open ASCII Report dialog and dismiss with Cancel (or complete Generate if safe in test env).
3. Click Download WITSML Report and observe generation/download behavior.
**Expected Results**
1. WITSML action button is available.
2. ASCII dialog interaction completes without leaving Reports controls broken.
3. WITSML download still initiates successfully with no regression from the ASCII dialog path.

### Verify Import from XOPS remains available on Material Usage after ASCII dialog
**Label:** Regression
**is_regression:** true
**is_sanity:** false
**Steps**
1. Open Reports and select the Material Usage tab.
2. Confirm Import from XOPS is visible, then open and Cancel the ASCII Report dialog.
3. Confirm Import from XOPS is still visible and clickable (non-Operator).
**Expected Results**
1. Material Usage tab shows Import from XOPS with ASCII Report and other actions.
2. ASCII dialog opens and dismisses cleanly.
3. Import from XOPS remains available and is not hidden or disabled by the ASCII dialog flow.
