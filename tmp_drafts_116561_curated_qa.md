STORY: FracPro Live+ Reports - Generate ASCII Report using saved channel configuration
US: 116561
COUNT: 27
NOTE: Dry-run drafts — not uploaded to ADO
CODEBASE: D:\Live_Plus_QA\fracpro-agile
STATE: QA | Existing linked TCs: 0 | Fresh suite
SCOPE: US-116561 saved channel configuration generate flow (5 AC scenarios)
RULE 13 MIX: Critical 3 / Regression 8

## Gaps (US vs QA codebase)
- IMPLEMENTED: loadReportSetup via GET .../reportSetup (getAvailablePlots); defaults for empty asciirealtime/asciifp.
- IMPLEMENTED: onGenerate compares selections; updateReportSetup when changed; skip update when unchanged; then COMMAND.
- IMPLEMENTED: PUT path is actually POST /v1/Wells/{wellId}/reportSetup — preserves other reportSetup fields via spread.
- IMPLEMENTED: Cancel/X emit cancelled without update/COMMAND; PUT failure toast blocks COMMAND; COMMAND errors via handleError.
- GAP-1 (HTTP method): AC says PUT reportSetup; code uses POST updateReportSetup — confirm with API contract/BA.
- GAP-2 (Wording): AC uses FrPro; UI tab label is FracPro.
- GAP-3 (Cancel during save): Cancel/X disabled while isGenerating during updateReportSetup.
- GAP-4 (GET naming): AC says GET reportSetup; client method is getAvailablePlots() hitting same reportSetup endpoint.
- Rule 12: auto feature_found=false on broad scan, but related ASCII dialog/generate flow is clearly present — generating from related implementation.

## Label summary

### Critical / Sanity (3)
- TC-3: Verify missing or empty asciirealtime selects all Real-time channels by default
- TC-4: Verify missing or empty asciifp selects no FracPro channels by default
- TC-5: Verify Generate with changed Real-time selection updates asciirealtime then invokes COMMAND

### Regression (8)
- TC-16: Verify close X dismisses dialog without saving channel configuration
- TC-17: Verify Real-time and FracPro tabs are available for channel configuration in ASCII dialog
- TC-18: Verify Generate and Cancel actions are available to complete ASCII configuration flow
- TC-19: Verify clicking ASCII Report opens configuration dialog before any COMMAND call
- TC-22: Verify Word Report generation still works after ASCII Generate with config save
- TC-23: Verify WITSML download still initiates after ASCII saved-channel Generate completes
- TC-24: Verify Reports Save still works after Cancel of ASCII configuration dialog
- TC-25: Verify ASCII generation uses current Reports wellId and treatmentId

### Standard
- TC-1: Verify GET reportSetup loads saved asciirealtime into Real-time channel selections
- TC-2: Verify GET reportSetup loads saved asciifp into FracPro channel selections
- TC-6: Verify Generate with changed FracPro selection updates asciifp then invokes COMMAND
- TC-7: Verify reportSetup update preserves non-ASCII properties when saving channel selection
- TC-8: Verify COMMAND runs only after successful reportSetup update when selection changed
- TC-9: Verify reopening dialog after successful Generate shows last saved channel configuration
- TC-10: Verify Generate with unchanged selections skips reportSetup update and calls COMMAND directly
- TC-11: Verify unchanged Generate still completes ASCII report generation via COMMAND
- TC-12: Verify failed reportSetup update shows error and does not invoke COMMAND
- TC-13: Verify COMMAND failure shows generation error after configuration path completes
- TC-14: Verify Cancel closes dialog without reportSetup update or COMMAND
- TC-15: Verify Cancel discards unsaved channel selection changes on next open
- TC-20: Verify select-all Real-time change is persisted to asciirealtime on Generate
- TC-21: Verify clearing all FracPro selections persists cleared asciifp on Generate
- TC-26: Verify Generate with both Real-time and FracPro changes updates asciirealtime and asciifp together
- TC-27: Verify Generate is disabled while ASCII channel lists are still loading

---

### TC-1: Verify GET reportSetup loads saved asciirealtime into Real-time channel selections
**Label:** Standard
**Steps**
1. Prepare a well whose reportSetup has non-empty asciirealtime values.
2. Open the ASCII Report dialog.
3. Inspect Real-time tab selections after load.
**Expected Results**
1. Saved asciirealtime exists in reportSetup.
2. GET reportSetup is called when the dialog opens.
3. Real-time checkboxes match saved asciirealtime channel names.

### TC-2: Verify GET reportSetup loads saved asciifp into FracPro channel selections
**Label:** Standard
**Steps**
1. Prepare a well whose reportSetup has non-empty asciifp values.
2. Open the ASCII Report dialog and open the FracPro tab.
3. Inspect FracPro tab selections after load.
**Expected Results**
1. Saved asciifp exists in reportSetup.
2. FracPro channel list is shown.
3. FracPro checkboxes match saved asciifp channel names.

### TC-3: Verify missing or empty asciirealtime selects all Real-time channels by default
**Label:** Critical
**Steps**
1. Use a well where asciirealtime is missing or empty.
2. Open the ASCII Report dialog on the Real-time tab.
3. Check selection state of listed Real-time channels.
**Expected Results**
1. GET reportSetup returns missing or empty asciirealtime.
2. Real-time channels load.
3. All Real-time channels are selected by default.

### TC-4: Verify missing or empty asciifp selects no FracPro channels by default
**Label:** Critical
**Steps**
1. Use a well where asciifp is missing or empty.
2. Open the ASCII Report dialog on the FracPro tab.
3. Check selection state of listed FracPro channels.
**Expected Results**
1. GET reportSetup returns missing or empty asciifp.
2. FracPro channels load.
3. No FracPro channels are selected by default.

### TC-5: Verify Generate with changed Real-time selection updates asciirealtime then invokes COMMAND
**Label:** Critical
**Steps**
1. Open ASCII Report dialog with known saved Real-time selections.
2. Change one or more Real-time channel checkboxes.
3. Click Generate and monitor reportSetup update then COMMAND.
**Expected Results**
1. Dialog shows current saved Real-time selections.
2. Selection differs from initial asciirealtime.
3. reportSetup update is called with new asciirealtime; after success COMMAND GenerateASCII runs.

### TC-6: Verify Generate with changed FracPro selection updates asciifp then invokes COMMAND
**Label:** Standard
**Steps**
1. Open ASCII Report dialog and change one or more FracPro channel selections.
2. Click Generate.
3. Monitor reportSetup update payload and subsequent COMMAND.
**Expected Results**
1. FracPro selections are modified.
2. reportSetup update includes updated asciifp.
3. After successful update, COMMAND GenerateASCII is invoked.

### TC-7: Verify reportSetup update preserves non-ASCII properties when saving channel selection
**Label:** Standard
**Steps**
1. Note existing reportSetup non-ASCII fields such as Plots, WarnDupPlots, Options.
2. Change ASCII channel selections and click Generate.
3. Inspect the update payload sent to reportSetup.
**Expected Results**
1. Baseline non-ASCII reportSetup values are known.
2. Generate with changed selections triggers update.
3. Payload spreads existing reportSetup and only replaces asciirealtime/asciifp.

### TC-8: Verify COMMAND runs only after successful reportSetup update when selection changed
**Label:** Standard
**Steps**
1. Change channel selections in ASCII dialog.
2. Click Generate and observe call order.
3. Confirm COMMAND does not start before update success.
**Expected Results**
1. Selections changed.
2. reportSetup update is issued first.
3. COMMAND GenerateASCII starts only after update success callback.

### TC-9: Verify reopening dialog after successful Generate shows last saved channel configuration
**Label:** Standard
**Steps**
1. Change selections, Generate successfully, and wait for flow to complete.
2. Open ASCII Report dialog again.
3. Compare Real-time and FracPro selections to the values just saved.
**Expected Results**
1. Generate completes with saved configuration.
2. Dialog reopens and loads reportSetup.
3. Selections match the last saved asciirealtime and asciifp.

### TC-10: Verify Generate with unchanged selections skips reportSetup update and calls COMMAND directly
**Label:** Standard
**Steps**
1. Open ASCII Report dialog without changing any channel selections.
2. Click Generate.
3. Monitor whether reportSetup update is skipped and COMMAND still runs.
**Expected Results**
1. Dialog opens with current saved selections.
2. No reportSetup update call is made.
3. COMMAND GenerateASCII is invoked directly.

### TC-11: Verify unchanged Generate still completes ASCII report generation via COMMAND
**Label:** Standard
**Steps**
1. Open ASCII dialog with unchanged selections and click Generate.
2. Wait for SignalR/COMMAND GenerateASCII completion.
3. Confirm ASCII download or success path proceeds.
**Expected Results**
1. Generate starts COMMAND without reportSetup update.
2. COMMAND/SignalR path runs for GenerateASCII.
3. ASCII report generation completes or download begins on success.

### TC-12: Verify failed reportSetup update shows error and does not invoke COMMAND
**Label:** Standard
**Steps**
1. Change channel selections in ASCII dialog.
2. Simulate or observe reportSetup update API failure on Generate.
3. Confirm error message and that COMMAND is not started.
**Expected Results**
1. Selection changes are made.
2. Error toast Failed to update ASCII channel selection is shown.
3. COMMAND GenerateASCII is not invoked.

### TC-13: Verify COMMAND failure shows generation error after configuration path completes
**Label:** Standard
**Steps**
1. Trigger Generate with valid/unchanged or successfully saved configuration.
2. Simulate or observe COMMAND/SignalR GenerateASCII failure.
3. Confirm error feedback to the user.
**Expected Results**
1. Generate path reaches COMMAND.
2. COMMAND/SignalR returns error for GenerateASCII.
3. Error toast indicates report generation was unsuccessful and ASCII button recovers.

### TC-14: Verify Cancel closes dialog without reportSetup update or COMMAND
**Label:** Standard
**Steps**
1. Open ASCII Report dialog.
2. Optionally change channel selections then click Cancel.
3. Monitor network for reportSetup update and COMMAND calls.
**Expected Results**
1. Dialog is open.
2. Cancel closes the dialog.
3. No reportSetup update and no COMMAND GenerateASCII are invoked.

### TC-15: Verify Cancel discards unsaved channel selection changes on next open
**Label:** Standard
**Steps**
1. Open ASCII dialog and change Real-time/FracPro selections.
2. Click Cancel.
3. Reopen ASCII dialog and inspect selections.
**Expected Results**
1. Unsaved selection changes were made.
2. Dialog closes on Cancel.
3. Reopened dialog shows previously saved selections only.

### TC-16: Verify close X dismisses dialog without saving channel configuration
**Label:** Regression
**Steps**
1. Open ASCII dialog and change selections.
2. Click the header close X control.
3. Confirm dialog closes without reportSetup update or COMMAND.
**Expected Results**
1. Selections were changed.
2. X closes the dialog.
3. No save and no COMMAND occur.

### TC-17: Verify Real-time and FracPro tabs are available for channel configuration in ASCII dialog
**Label:** Regression
**Steps**
1. Open the ASCII Report dialog.
2. Inspect available tabs.
3. Switch between Real-time and FracPro tabs.
**Expected Results**
1. Dialog opens.
2. Real-time and FracPro tabs are visible.
3. Each tab shows its channel selection grid.

### TC-18: Verify Generate and Cancel actions are available to complete ASCII configuration flow
**Label:** Regression
**Steps**
1. Open the ASCII Report dialog.
2. Locate footer action buttons.
3. Confirm Generate and Cancel are present and enabled after load.
**Expected Results**
1. Dialog opens.
2. Generate and Cancel buttons are visible.
3. After loading completes, Generate and Cancel are usable.

### TC-19: Verify clicking ASCII Report opens configuration dialog before any COMMAND call
**Label:** Regression
**Steps**
1. On Reports click ASCII Report.
2. Monitor network for COMMAND on the click.
3. Confirm configuration dialog opens first.
**Expected Results**
1. ASCII Report button is clicked.
2. No COMMAND call occurs on open alone.
3. ASCII configuration dialog is shown.

### TC-20: Verify select-all Real-time change is persisted to asciirealtime on Generate
**Label:** Standard
**Steps**
1. Open ASCII dialog on Real-time tab.
2. Use select-all to change Real-time selections, then Generate.
3. Confirm reportSetup update contains the select-all result for asciirealtime.
**Expected Results**
1. Real-time channels are listed.
2. Select-all changes selection state.
3. Updated asciirealtime is saved then COMMAND runs.

### TC-21: Verify clearing all FracPro selections persists cleared asciifp on Generate
**Label:** Standard
**Steps**
1. Open ASCII dialog with some FracPro channels previously selected.
2. Clear all FracPro selections and click Generate.
3. Inspect reportSetup update asciifp value.
**Expected Results**
1. Prior FracPro selections existed.
2. All FracPro selections are cleared.
3. asciifp is saved as empty list then COMMAND runs.

### TC-22: Verify Word Report generation still works after ASCII Generate with config save
**Label:** Regression
**Steps**
1. Complete an ASCII Generate that updates channel configuration.
2. Click Download Word Report.
3. Confirm Word report generation still initiates.
**Expected Results**
1. ASCII generate with save completes.
2. Word Report button remains usable.
3. Word report COMMAND/download flow still works.

### TC-23: Verify WITSML download still initiates after ASCII saved-channel Generate completes
**Label:** Regression
**Steps**
1. Complete ASCII Generate using saved or updated channel configuration.
2. Click Download WITSML Report.
3. Confirm WITSML flow still starts.
**Expected Results**
1. ASCII flow completes.
2. WITSML button is clickable.
3. WITSML generation/download still works.

### TC-24: Verify Reports Save still works after Cancel of ASCII configuration dialog
**Label:** Regression
**Steps**
1. Open ASCII dialog, change selections, Cancel.
2. Click Save on Reports.
3. Confirm Save still functions.
**Expected Results**
1. ASCII dialog cancelled without save.
2. Save button is available.
3. Reports Save still works without regression.

### TC-25: Verify ASCII generation uses current Reports wellId and treatmentId
**Label:** Regression
**Steps**
1. Note current wellId and treatmentId on Reports.
2. Open ASCII dialog and Generate.
3. Confirm COMMAND payload uses those well and treatment ids.
**Expected Results**
1. Current well/treatment context is known.
2. Generate runs.
3. GenerateASCII COMMAND uses the current Reports wellId and treatmentId.

### TC-26: Verify Generate with both Real-time and FracPro changes updates asciirealtime and asciifp together
**Label:** Standard
**Steps**
1. Open ASCII Report dialog and change selections on Real-time and FracPro tabs.
2. Click Generate.
3. Inspect reportSetup update payload and subsequent COMMAND.
**Expected Results**
1. Both Real-time and FracPro selections differ from saved values.
2. Single reportSetup update includes both asciirealtime and asciifp.
3. After successful update, COMMAND GenerateASCII runs once.

### TC-27: Verify Generate is disabled while ASCII channel lists are still loading
**Label:** Standard
**Steps**
1. Open the ASCII Report dialog.
2. While loading skeleton is visible, attempt to click Generate.
3. Wait for load to finish and confirm Generate becomes enabled.
**Expected Results**
1. Dialog opens in loading state.
2. Generate remains disabled while isLoading is true.
3. After channels and reportSetup load, Generate is enabled for use.
