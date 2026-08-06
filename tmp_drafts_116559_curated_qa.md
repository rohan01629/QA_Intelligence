STORY: FracPro Live+ - Reports- Rename Download ASCII Report button and launch ASCII Report dialog
US: 116559
COUNT: 25
NOTE: Dry-run drafts — not uploaded to ADO
CODEBASE: D:\Live_Plus_QA\fracpro-agile
STATE: QA | Existing linked TCs: 0
RULE 13 MIX: Critical 3 / Regression 8

## Gaps (US vs QA codebase)
- IMPLEMENTED (QA): onOpenAsciiReportDialog opens modal; COMMAND only on Generate via startAsciiCommand.
- IMPLEMENTED: Button label 'ASCII Report' via BUTTON.DOWNLOAD_ASCII_REPORT translation in en.json.
- IMPLEMENTED: Real-time + FracPro tabs, Generate/Cancel, shared report-buttons on all 3 report tabs.
- GAP-1 (Label wording): AC says FrPro tab; UI shows 'FracPro' — minor text mismatch.
- GAP-2 (Generate unchanged): Generate with no selection change skips updateReportSetup but still runs COMMAND.
- GAP-3 (Cancel during save): Cancel/close disabled while isGenerating — user cannot dismiss mid updateReportSetup.
- GAP-4 (Backdrop): modal uses backdrop static + keyboard false — outside click/Escape may not dismiss (X/Cancel work).
- UAT: legacy direct GenerateASCII on click may still exist until QA build is promoted.

## Label summary

### Critical / Sanity (3)
- TC-1: Verify ASCII Report button label on Word Report tab
- TC-4: Verify clicking ASCII Report opens dialog without invoking COMMAND API
- TC-11: Verify Generate saves changed channel selection then starts ASCII generation

### Regression (8)
- TC-18: Verify Download Word Report button still works after ASCII dialog cancel
- TC-19: Verify Download WITSML Report button still works after ASCII dialog flow
- TC-20: Verify Save button on Reports still works after ASCII dialog interaction
- TC-21: Verify ASCII dialog shows loading skeleton while channels are fetched
- TC-22: Verify ASCII dialog Cancel is disabled while reportSetup update is in progress
- TC-23: Verify ASCII Report flow on Material Usage tab preserves Import from XOPS button
- TC-24: Verify default Real-time selection uses all channels when no saved asciirealtime exists
- TC-25: Verify default FracPro selection is none when no saved asciifp exists

### Standard
- TC-2: Verify ASCII Report button label on Material Usage tab
- TC-3: Verify ASCII Report button label on Post Job Data tab
- TC-5: Verify ASCII Report modal dialog title and layout
- TC-6: Verify Real-time tab is present and active by default in ASCII dialog
- TC-7: Verify FracPro tab switches channel list in ASCII dialog
- TC-8: Verify Generate and Cancel action buttons are present in ASCII dialog
- TC-9: Verify Cancel dismisses ASCII dialog without saving reportSetup changes
- TC-10: Verify close X dismisses ASCII dialog without saving changes
- TC-12: Verify Generate with unchanged selections still closes dialog and runs COMMAND
- TC-13: Verify Real-time channel list loads with selectable checkboxes
- TC-14: Verify FracPro channel list loads with selectable checkboxes
- TC-15: Verify select-all toggles all Real-time channels in ASCII dialog
- TC-16: Verify failed reportSetup update shows error and does not start COMMAND
- TC-17: Verify Operator role cannot click ASCII Report button

---

### TC-1: Verify ASCII Report button label on Word Report tab
**Label:** Critical
**Steps**
1. Open Reports and select the Word Report (Plots in word Report) tab.
2. Locate the ASCII Report action button in the report buttons row.
3. Read the visible button label text.
**Expected Results**
1. Word Report tab is active.
2. ASCII Report button is visible.
3. Button label displays 'ASCII Report' not 'Download ASCII Report'.

### TC-2: Verify ASCII Report button label on Material Usage tab
**Label:** Standard
**Steps**
1. Open Reports and select the Material Usage tab.
2. Locate the ASCII Report button.
3. Read the visible button label.
**Expected Results**
1. Material Usage tab is active.
2. ASCII Report button is visible.
3. Button label displays 'ASCII Report'.

### TC-3: Verify ASCII Report button label on Post Job Data tab
**Label:** Standard
**Steps**
1. Open Reports and select the Post Job Data tab.
2. Locate the ASCII Report button.
3. Read the visible button label.
**Expected Results**
1. Post Job Data tab is active.
2. ASCII Report button is visible.
3. Button label displays 'ASCII Report'.

### TC-4: Verify clicking ASCII Report opens dialog without invoking COMMAND API
**Label:** Critical
**Steps**
1. On any Reports tab click the ASCII Report button once.
2. Monitor network/API for COMMAND or GenerateASCII invocation on click.
3. Observe whether the ASCII Report modal opens.
**Expected Results**
1. Button click is accepted.
2. No COMMAND/GenerateASCII API call occurs on button click alone.
3. ASCII Report modal dialog opens via onOpenAsciiReportDialog.

### TC-5: Verify ASCII Report modal dialog title and layout
**Label:** Standard
**Steps**
1. Click ASCII Report on Reports.
2. Inspect modal header title and overall dialog structure.
3. Confirm modal is centered and sized appropriately.
**Expected Results**
1. Modal opens.
2. Dialog title shows 'ASCII Report'.
3. Modal presents tab area and action buttons at bottom.

### TC-6: Verify Real-time tab is present and active by default in ASCII dialog
**Label:** Standard
**Steps**
1. Open the ASCII Report dialog.
2. Inspect tab labels and active tab state.
3. Confirm Real-time channel spreadsheet is shown.
**Expected Results**
1. Dialog opens.
2. Real-time and FracPro tabs are visible.
3. Real-time tab is active by default with channel selection grid.

### TC-7: Verify FracPro tab switches channel list in ASCII dialog
**Label:** Standard
**Steps**
1. Open the ASCII Report dialog.
2. Click the FracPro tab.
3. Inspect the channel selection grid content.
**Expected Results**
1. Dialog opens on Real-time tab.
2. FracPro tab becomes active.
3. FracPro channel spreadsheet is displayed (AC note says FrPro; UI label is FracPro).

### TC-8: Verify Generate and Cancel action buttons are present in ASCII dialog
**Label:** Standard
**Steps**
1. Open the ASCII Report dialog.
2. Inspect footer action buttons.
3. Confirm button labels.
**Expected Results**
1. Dialog opens.
2. Cancel and Generate buttons are visible.
3. Cancel uses translated CANCEL label; Generate shows 'Generate'.

### TC-9: Verify Cancel dismisses ASCII dialog without saving reportSetup changes
**Label:** Standard
**Steps**
1. Open ASCII Report dialog and change Real-time channel selections.
2. Click Cancel.
3. Reopen ASCII dialog and compare selections to saved state before changes.
**Expected Results**
1. Channel selections were changed in dialog.
2. Dialog closes on Cancel.
3. Reopened dialog shows prior saved selections; unsaved dialog edits were discarded.

### TC-10: Verify close X dismisses ASCII dialog without saving changes
**Label:** Standard
**Steps**
1. Open ASCII Report dialog and toggle FracPro channel selections.
2. Click the header close (X) control.
3. Reopen dialog and verify selections were not persisted from cancelled session.
**Expected Results**
1. Selections were changed.
2. Dialog closes via X without save.
3. Prior saved channel selections are restored on reopen.

### TC-11: Verify Generate saves changed channel selection then starts ASCII generation
**Label:** Critical
**Steps**
1. Open ASCII Report dialog and change Real-time and/or FracPro channel selections.
2. Click Generate.
3. Monitor updateReportSetup call and subsequent COMMAND/GenerateASCII flow.
**Expected Results**
1. Selections are modified.
2. updateReportSetup is called with asciirealtime/asciifp when selection changed.
3. Dialog closes and ASCII generation COMMAND flow starts after successful save.

### TC-12: Verify Generate with unchanged selections still closes dialog and runs COMMAND
**Label:** Standard
**Steps**
1. Open ASCII Report dialog without changing any channel selections.
2. Click Generate.
3. Observe whether updateReportSetup is skipped and COMMAND still runs.
**Expected Results**
1. Dialog opens with current saved selections.
2. Generate closes dialog without updateReportSetup when selection unchanged.
3. startAsciiCommand still invokes GenerateASCII COMMAND path.

### TC-13: Verify Real-time channel list loads with selectable checkboxes
**Label:** Standard
**Steps**
1. Open ASCII Report dialog on Real-time tab.
2. Wait for loading skeleton to complete.
3. Inspect channel rows and Select checkboxes.
**Expected Results**
1. Loading state completes.
2. Real-time channels populate in spreadsheet.
3. Each row has Channel name and Select checkbox.

### TC-14: Verify FracPro channel list loads with selectable checkboxes
**Label:** Standard
**Steps**
1. Open ASCII Report dialog and switch to FracPro tab.
2. Wait for channel data to load.
3. Toggle individual channel Select checkboxes.
**Expected Results**
1. FracPro tab shows channel grid after load.
2. Channels are listed with Select checkboxes.
3. Individual checkbox toggles update row selection state.

### TC-15: Verify select-all toggles all Real-time channels in ASCII dialog
**Label:** Standard
**Steps**
1. Open ASCII Report dialog on Real-time tab with multiple channels.
2. Use select-all in the Select column header.
3. Confirm all Real-time rows reflect the select-all state.
**Expected Results**
1. Multiple Real-time channels are listed.
2. Select-all control is available.
3. All Real-time channel checkboxes match select-all on/off state.

### TC-16: Verify failed reportSetup update shows error and does not start COMMAND
**Label:** Standard
**Steps**
1. Open ASCII Report dialog and change channel selections.
2. Simulate or observe updateReportSetup API failure on Generate.
3. Confirm dialog behavior and COMMAND not started.
**Expected Results**
1. Selection changes are made.
2. Error toast 'Failed to update ASCII channel selection' is shown.
3. GenerateASCII COMMAND does not start; dialog remains or user can retry.

### TC-17: Verify Operator role cannot click ASCII Report button
**Label:** Standard
**Steps**
1. Log in as Operator user and open Reports.
2. Attempt to click the ASCII Report button.
3. Observe disabled state and pointer behavior.
**Expected Results**
1. Reports page loads for Operator.
2. ASCII Report button is disabled with reduced opacity.
3. Click does not open dialog or start generation.

### TC-20: Verify Save button on Reports still works after ASCII dialog interaction
**Label:** Regression
**Steps**
1. Make a report change on Material Usage tab.
2. Open and Cancel ASCII Report dialog.
3. Click Save on Reports.
**Expected Results**
1. Pending report edits exist.
2. ASCII dialog cancelled.
3. Save still triggers report save workflow without regression.

### TC-21: Verify ASCII dialog shows loading skeleton while channels are fetched
**Label:** Regression
**Steps**
1. Click ASCII Report on a well/treatment with channel data.
2. Observe dialog immediately after open before data loads.
3. Confirm skeleton transitions to channel grid.
**Expected Results**
1. Dialog opens quickly.
2. Placeholder skeleton rows appear during isLoading.
3. Channel spreadsheet replaces skeleton when data is ready.

### TC-22: Verify ASCII dialog Cancel is disabled while reportSetup update is in progress
**Label:** Regression
**Steps**
1. Open ASCII Report dialog and change channel selections.
2. Click Generate to trigger updateReportSetup.
3. While isGenerating attempt Cancel or close X.
**Expected Results**
1. Generate starts save path.
2. Cancel and close controls are disabled during isGenerating.
3. Document behavior: user cannot cancel mid-save (potential UX gap vs AC close-anytime expectation).



### TC-24: Verify default Real-time selection uses all channels when no saved asciirealtime exists
**Label:** Regression
**Steps**
1. Use a well with no prior ASCII Real-time selection saved in reportSetup.
2. Open ASCII Report dialog on Real-time tab.
3. Inspect initial checkbox states.
**Expected Results**
1. Report setup has empty/null asciirealtime.
2. Dialog loads Real-time channels.
3. All Real-time channels are selected by default per implementation.

### TC-25: Verify default FracPro selection is none when no saved asciifp exists
**Label:** Regression
**Steps**
1. Use a well with no prior FracPro ASCII selection in reportSetup.
2. Open ASCII Report dialog and switch to FracPro tab.
3. Inspect initial checkbox states.
**Expected Results**
1. Report setup has empty/null asciifp.
2. FracPro channels load in grid.
3. FracPro channels are unchecked by default per implementation.
