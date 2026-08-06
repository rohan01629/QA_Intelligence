STORY: FracPro Live+ - Reports - Load and display Real-time and FracPro channel selections
US: 116560
COUNT: 28
NOTE: Dry-run curated drafts — not uploaded to ADO
SOURCE: AC + local code (GET `{wellId}/reportSetup` in report.service.ts; ASCII channel dialog / asciirealtime / asciifp UI not found yet)
---

### TC-1: Verify opening ASCII Report dialog invokes GET reportSetup
**Steps**
1. Open Reports for a well/treatment and open the ASCII Report dialog.
2. Capture the outbound HTTP request on dialog open.
3. Inspect the request method and path.
**Expected Results**
1. ASCII Report dialog open is triggered.
2. An HTTP GET is issued.
3. Request targets the reportSetup API for the current well (`…/{wellId}/reportSetup`).

### TC-2: Verify dialog shows Real-time and FracPro tabs
**Steps**
1. Open the ASCII Report dialog after reportSetup returns successfully.
2. Inspect available tabs.
3. Select each tab once.
**Expected Results**
1. Dialog loads.
2. Two tabs are present: Real-time and FracPro.
3. Each tab can be activated and displays its column content.

### TC-3: Verify Real-time tab columns #, Channel, Select
**Steps**
1. Open ASCII Report dialog and select Real-time tab.
2. Inspect grid/table headers.
3. Confirm row content structure.
**Expected Results**
1. Real-time tab is active.
2. Columns include #, Channel, and Select.
3. Each Real-time channel row shows index/name and a checkbox.

### TC-4: Verify FracPro tab columns #, Channel, Select
**Steps**
1. Open ASCII Report dialog and select FracPro tab.
2. Inspect grid/table headers.
3. Confirm row content structure.
**Expected Results**
1. FracPro tab is active.
2. Columns include #, Channel, and Select.
3. Each FracPro channel row shows index/name and a checkbox.

### TC-5: Verify all Real-time channels are listed
**Steps**
1. Ensure reportSetup/channel source contains multiple Real-time channels.
2. Open dialog → Real-time tab.
3. Compare listed channels to available Real-time channel inventory.
**Expected Results**
1. Multiple Real-time channels exist in source data.
2. Real-time tab renders the channel list.
3. All available Real-time channels are displayed (none silently omitted).

### TC-6: Verify all FracPro channels are listed
**Steps**
1. Ensure source data contains multiple FracPro channels.
2. Open dialog → FracPro tab.
3. Compare listed channels to FracPro inventory.
**Expected Results**
1. Multiple FracPro channels exist.
2. FracPro tab renders the list.
3. All FracPro channels are displayed.

### TC-7: Verify Real-time header Select checkbox exists
**Steps**
1. Open dialog → Real-time tab.
2. Locate the header Select checkbox.
3. Observe enabled state when channels exist.
**Expected Results**
1. Real-time tab is visible.
2. Header Select checkbox is present.
3. Header control is usable when channels are listed.

### TC-8: Verify FracPro header Select checkbox exists
**Steps**
1. Open dialog → FracPro tab.
2. Locate the header Select checkbox.
3. Observe enabled state when channels exist.
**Expected Results**
1. FracPro tab is visible.
2. Header Select checkbox is present.
3. Header control is usable when channels are listed.

### TC-9: Verify asciirealtime values pre-select only those Real-time channels
**Steps**
1. Arrange reportSetup (or equivalent) so asciirealtime returns a subset of Real-time channel ids/names.
2. Open ASCII Report dialog → Real-time tab.
3. Inspect checkbox state for each Real-time channel.
**Expected Results**
1. asciirealtime contains a non-empty subset.
2. Dialog loads Real-time list.
3. Only channels in asciirealtime are selected; others are unchecked.

### TC-10: Verify missing/empty asciirealtime selects all Real-time channels by default
**Steps**
1. Arrange response with asciirealtime missing or empty.
2. Open dialog → Real-time tab.
3. Inspect all Real-time row checkboxes.
**Expected Results**
1. asciirealtime is absent/empty.
2. Real-time channels are listed.
3. All Real-time channels are selected by default.

### TC-11: Verify asciifp values pre-select only those FracPro channels
**Steps**
1. Arrange response so asciifp returns a subset of FracPro channels.
2. Open dialog → FracPro tab.
3. Inspect checkbox states.
**Expected Results**
1. asciifp contains a non-empty subset.
2. FracPro list loads.
3. Only asciifp channels are selected; others remain unchecked.

### TC-12: Verify missing/empty asciifp selects no FracPro channels by default
**Steps**
1. Arrange response with asciifp missing or empty.
2. Open dialog → FracPro tab.
3. Inspect all FracPro row checkboxes.
**Expected Results**
1. asciifp is absent/empty.
2. FracPro channels are listed.
3. No FracPro channels are selected by default.

### TC-13: Verify user can toggle an individual Real-time channel
**Steps**
1. Open dialog with default Real-time selections loaded.
2. Uncheck one selected Real-time channel.
3. Check a previously unchecked Real-time channel (if any).
**Expected Results**
1. Defaults are visible.
2. Individual uncheck updates that row only.
3. Individual check updates that row only; other rows unchanged.

### TC-14: Verify user can toggle an individual FracPro channel
**Steps**
1. Open dialog → FracPro tab with mixed selection possible.
2. Check one FracPro channel.
3. Uncheck that same channel.
**Expected Results**
1. FracPro tab is ready.
2. Channel becomes selected.
3. Channel becomes unselected; other rows unchanged.

### TC-15: Verify Real-time header Select selects all rows
**Steps**
1. Open Real-time tab with some channels unchecked.
2. Click header Select checkbox to select-all.
3. Inspect all row checkboxes.
**Expected Results**
1. Mixed/partial selection is visible.
2. Header Select-all is activated.
3. All Real-time channel checkboxes are selected.

### TC-16: Verify Real-time header Select clears all rows
**Steps**
1. Open Real-time tab with all/most channels selected.
2. Click header Select checkbox to clear.
3. Inspect all row checkboxes.
**Expected Results**
1. Channels are selected.
2. Header clear action is performed.
3. All Real-time channel checkboxes are cleared.

### TC-17: Verify FracPro header Select selects all rows
**Steps**
1. Open FracPro tab with channels listed and none/partial selected.
2. Click header Select to select-all.
3. Inspect row checkboxes.
**Expected Results**
1. FracPro channels are listed.
2. Select-all is activated.
3. All FracPro channels are selected.

### TC-18: Verify FracPro header Select clears all rows
**Steps**
1. Select all FracPro channels.
2. Click header Select to clear.
3. Inspect row checkboxes.
**Expected Results**
1. All FracPro channels selected.
2. Clear action runs.
3. No FracPro channels remain selected.

### TC-19: Verify tab switch preserves channel selections
**Steps**
1. On Real-time tab, change several checkbox selections.
2. Switch to FracPro tab and change selections.
3. Switch back to Real-time and review selections.
**Expected Results**
1. Real-time edits are applied.
2. FracPro edits are applied.
3. Real-time selections remain as edited after switching back.

### TC-20: Verify GET reportSetup failure shows error and does not fake channel lists
**Steps**
1. Force GET reportSetup to fail (500/network error).
2. Open ASCII Report dialog.
3. Observe error handling and grid content.
**Expected Results**
1. reportSetup failure is simulated.
2. Dialog open is attempted.
3. User sees existing error handling; channel grids are not populated with invented data.

### TC-21: Verify empty Real-time channel inventory UI
**Steps**
1. Arrange source with zero Real-time channels.
2. Open dialog → Real-time tab.
3. Observe empty-state / header checkbox behavior.
**Expected Results**
1. No Real-time channels available.
2. Real-time tab shows empty list/state.
3. No false selected rows; header Select does not imply channels exist.

### TC-22: Verify empty FracPro channel inventory UI
**Steps**
1. Arrange source with zero FracPro channels.
2. Open dialog → FracPro tab.
3. Observe empty-state behavior.
**Expected Results**
1. No FracPro channels available.
2. Empty list/state is shown.
3. Default “none selected” remains consistent.

### TC-23: Verify asciirealtime unknown channel ids are ignored safely
**Steps**
1. Return asciirealtime values that include an unknown/invalid channel id.
2. Open Real-time tab.
3. Inspect selection and absence of crash.
**Expected Results**
1. Payload includes invalid id plus valid ids.
2. Dialog loads.
3. Valid channels select correctly; invalid id does not break UI.

### TC-24: Verify asciifp unknown channel ids are ignored safely
**Steps**
1. Return asciifp with an unknown FracPro channel id.
2. Open FracPro tab.
3. Inspect selection/stability.
**Expected Results**
1. Invalid asciifp value present.
2. FracPro list loads.
3. UI remains stable; only valid matching channels are selected.

### TC-25: Verify Operator cannot modify ASCII channel selections (parity with report buttons)
**Steps**
1. Sign in as Operator and open Reports.
2. Attempt to open ASCII Report dialog / change channel checkboxes.
3. Observe allowed actions.
**Expected Results**
1. Operator session is active.
2. ASCII report controls follow existing operator disable pattern where applicable.
3. Operator cannot persist channel selection changes.

### TC-26: Verify Cancel closes dialog without persisting channel edits
**Steps**
1. Open dialog and change Real-time and FracPro selections.
2. Click Cancel.
3. Re-open dialog and compare selections to original defaults from reportSetup.
**Expected Results**
1. Edits are visible before cancel.
2. Dialog closes without save.
3. Re-open restores defaults from GET reportSetup (edits discarded).

### TC-27: Verify closing dialog (X) discards unsaved channel edits
**Steps**
1. Open dialog and modify channel checkboxes.
2. Close via dialog close control.
3. Re-open and verify selections.
**Expected Results**
1. Modifications are made.
2. Dialog dismisses.
3. Unsaved edits are not retained.

### TC-28: Verify current build gap — ASCII channel selection UI not implemented
**Steps**
1. Inspect Reports ASCII control in current Live_Plus_UAT build.
2. Search for asciirealtime / asciifp / ASCII channel dialog UI.
3. Confirm current click behavior vs story.
**Expected Results**
1. Button still labeled Download ASCII Report and calls GenerateASCII path today.
2. No ASCII Real-time/FracPro channel selection dialog found for asciirealtime/asciifp.
3. Feature gap vs US 116560 is documented for implementation tracking.

