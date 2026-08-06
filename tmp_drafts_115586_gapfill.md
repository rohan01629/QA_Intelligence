STORY: FracPro Live + General- Add Well Dropdown to Enable Switching Between Wells Within the Current Pad
US: 115586
COUNT: 25 (gap-fill — 53 TCs already linked)
NOTE: Dry-run drafts — not uploaded to ADO
CODEBASE: D:\Live_Plus_QA\fracpro-agile
DOTS: a2b9d7ab4 well dropdown red and green dot (origin/wtt/liveplus/QA)
AC: Scenarios 1–5 + Note (Active green / Complete red well dots) — dots implemented
RULE 13 MIX: Critical 3 / Regression 8

## Implementation gaps (code vs US)
- CORRECTED: Active/Complete well dots ARE implemented (commit a2b9d7ab4 on origin/wtt/liveplus/QA).
- Mapping: realtimewell truthy → green live-dot (Active); realtimewell falsy → red completed-dot (Complete).
- Shown in both ng-label-tmp (closed) and ng-option-tmp (open list) via well-option-row.
- NOTE: Local branch wtt/liveplus/qa-rohan may lag; analyze/pull origin/wtt/liveplus/QA for latest dots.
- Residual risk: Active/Complete is keyed off realtimewell only — if product defines Complete differently than !realtimewell, clarify with BA.
- IMPLEMENTED: Well ng-select switcher, pad filter/dedupe/sort, unsaved alert paths, MQTT keeps well enabled.
- ADO: 53 linked TCs; add gap-fill for dots + implementation edges not in 116089–116141.

## Label summary

### Critical (3)
- TC-1: Verify Well dropdown renders beside Pad label with current well selected on load
- TC-2: Verify Active realtime well shows green live-dot in Well dropdown options
- TC-11: Verify selecting another well loads that well and refreshes well-specific data

### Regression (8)
- TC-18: Verify Well Version and Stage stay enabled during MQTT Live Actual Treatment Schedule
- TC-19: Verify Version dropdown still works after repeated Well dropdown switches
- TC-20: Verify Reports data refreshes for newly selected well after header switch
- TC-21: Verify Plots templates refresh for newly selected well after header switch
- TC-22: Verify Material Selection and Treatment Schedule refresh after well switch
- TC-23: Verify well switch clears prior stage and treatment selection state
- TC-24: Verify Well dropdown hidden in fullscreen plot and restored after exit
- TC-25: Verify plot popout open does not break well switch context sync

### Standard
- TC-3: Verify non-realtime Complete well shows red completed-dot in Well dropdown options
- TC-4: Verify closed Well dropdown label also shows green or red status dot for selected well
- TC-5: Verify Active green and Complete red dots appear together when pad has both well types
- TC-6: Verify Well status dots use realtimewell and remain distinct from Stage inProgress dots
- TC-7: Verify Well dropdown lists only current-pad wells and excludes other pads
- TC-8: Verify Well dropdown search filters pad wells by typed well name
- TC-9: Verify Well dropdown pad wells are alphabetically sorted by wellName
- TC-10: Verify duplicate wellName and wellAPI pairs are deduplicated in Well list
- TC-12: Verify Cancel on unsaved-changes alert reverts Well dropdown to previous well
- TC-13: Verify Discard on unsaved-changes alert completes switch to selected well
- TC-14: Verify Save on unsaved-changes alert then switches to the newly selected well
- TC-15: Verify padName stays unchanged in header and storage after well switch
- TC-16: Verify refresh keeps Well selection and status dot via originalWellId
- TC-17: Verify selecting same current well is a no-op and does not reload

---

### TC-1: Verify Well dropdown renders beside Pad label with current well selected on load
**Label:** Critical
**Steps**
1. Open a pad with one or more wells and load Well & Treatment.
2. Inspect left sub-menubar: Pad label and Well control.
3. Confirm Well dropdown selected value matches the active well.
**Expected Results**
1. Pad/well context loads.
2. Well ng-select appears next to Pad (left cluster); Version remains on the right.
3. Current well is selected by default.

### TC-2: Verify Active realtime well shows green live-dot in Well dropdown options
**Label:** Critical
**Steps**
1. Open a pad that includes a realtime/Active well (realtimewell truthy).
2. Expand the Well dropdown and locate that well row.
3. Inspect the status indicator beside the well name.
**Expected Results**
1. Realtime/Active well is listed.
2. Option row is visible with well name.
3. Green live-dot is shown for the Active/realtime well.

### TC-3: Verify non-realtime Complete well shows red completed-dot in Well dropdown options
**Label:** Standard
**Steps**
1. Open a pad that includes a non-realtime Complete well (realtimewell falsy).
2. Expand the Well dropdown and locate that well row.
3. Inspect the status indicator beside the well name.
**Expected Results**
1. Complete/non-realtime well is listed.
2. Option row is visible with well name.
3. Red completed-dot is shown for the Complete well.

### TC-4: Verify closed Well dropdown label also shows green or red status dot for selected well
**Label:** Standard
**Steps**
1. Select an Active realtime well and close the dropdown.
2. Inspect the closed Well control label for a green live-dot.
3. Select a Complete non-realtime well and inspect the closed label for a red completed-dot.
**Expected Results**
1. Active well selected.
2. Closed label shows green live-dot for realtimewell.
3. Closed label shows red completed-dot when selected well is not realtime.

### TC-5: Verify Active green and Complete red dots appear together when pad has both well types
**Label:** Standard
**Steps**
1. Open a pad containing both realtime Active and non-realtime Complete wells.
2. Expand the Well dropdown.
3. Compare status dots across Active vs Complete rows.
**Expected Results**
1. Both well types are listed.
2. Dropdown options show status indicators.
3. Active rows show green live-dot; Complete rows show red completed-dot.

### TC-6: Verify Well status dots use realtimewell and remain distinct from Stage inProgress dots
**Label:** Standard
**Steps**
1. Expand the Well dropdown and note green/red dots driven by well realtimewell.
2. Expand the Stage dropdown and note live/completed dots driven by stage inProgress.
3. Confirm both controls show their own status indicators independently.
**Expected Results**
1. Well dots reflect realtimewell Active/Complete status.
2. Stage dots reflect inProgress status.
3. Well and Stage status indicators operate independently without conflict.

### TC-7: Verify Well dropdown lists only current-pad wells and excludes other pads
**Label:** Standard
**Steps**
1. Open pad A with known wells.
2. Expand the Well dropdown and list all well names.
3. Confirm no wells belonging only to other pads appear.
**Expected Results**
1. Pad A context is active.
2. Dropdown lists pad A wells with status dots as applicable.
3. Other-pad wells are excluded.

### TC-8: Verify Well dropdown search filters pad wells by typed well name
**Label:** Standard
**Steps**
1. Open a multi-well pad and expand Well dropdown.
2. Type a partial well name into the searchable input.
3. Select a matching well from filtered results.
**Expected Results**
1. Full list available before search.
2. List filters to matching names; status dots remain on visible rows.
3. Matching well can be selected.

### TC-9: Verify Well dropdown pad wells are alphabetically sorted by wellName
**Label:** Standard
**Steps**
1. Open a multi-well pad.
2. Expand Well dropdown without typing a search.
3. Read well names top to bottom.
**Expected Results**
1. Multi-well pad loaded.
2. List opens.
3. Names are sorted alphabetically by wellName.

### TC-10: Verify duplicate wellName and wellAPI pairs are deduplicated in Well list
**Label:** Standard
**Steps**
1. Use a pad where source data could return duplicate wellName|wellAPI rows.
2. Open the Well dropdown.
3. Count duplicate physical well entries.
**Expected Results**
1. Pad loads.
2. Dropdown opens.
3. Each wellName|wellAPI key appears once.

### TC-11: Verify selecting another well loads that well and refreshes well-specific data
**Label:** Critical
**Steps**
1. On well A note visible well-specific header/data and status dot.
2. Select well B from the Well dropdown and wait for navigation/reload.
3. Confirm URL/header/data and status dot reflect well B.
**Expected Results**
1. Well A baseline noted.
2. Well B change path runs.
3. Well B loads with refreshed data; pad unchanged; status dot matches well B realtimewell.

### TC-12: Verify Cancel on unsaved-changes alert reverts Well dropdown to previous well
**Label:** Standard
**Steps**
1. On well A make an unsaved change.
2. Select well B from Well dropdown.
3. Cancel/dismiss the unsaved-changes alert without Save or Discard.
4. Inspect Well dropdown selection and status dot.
**Expected Results**
1. Unsaved state exists on well A.
2. Alert appears.
3. User cancels.
4. Dropdown reverts to well A with well A status dot.

### TC-13: Verify Discard on unsaved-changes alert completes switch to selected well
**Label:** Standard
**Steps**
1. On well A make an unsaved change.
2. Select well B from Well dropdown.
3. Choose Discard on the alert.
4. Confirm well B becomes active.
**Expected Results**
1. Unsaved state exists.
2. Alert appears.
3. Discard chosen.
4. Well B loads and data refreshes.

### TC-14: Verify Save on unsaved-changes alert then switches to the newly selected well
**Label:** Standard
**Steps**
1. On well A with owned/single version, make an unsaved change.
2. Select well B from Well dropdown.
3. Choose Save on the alert and wait for save path.
4. Confirm well B is active afterward.
**Expected Results**
1. Editable owned/single-version context on well A.
2. Alert appears.
3. Save completes.
4. Well B loads; pad remains the same.

### TC-15: Verify padName stays unchanged in header and storage after well switch
**Label:** Standard
**Steps**
1. Record Pad header text and padName storage for pad A / well A.
2. Switch to well B via Well dropdown.
3. Re-check Pad header and padName storage.
**Expected Results**
1. Baseline pad name recorded.
2. Well B loads.
3. Pad name unchanged; only well selection changes.

### TC-16: Verify refresh keeps Well selection and status dot via originalWellId
**Label:** Standard
**Steps**
1. Switch to well B and wait until load completes; note its status dot.
2. Refresh the browser.
3. Inspect Well dropdown selected value and status dot after reload.
**Expected Results**
1. Well B active before refresh.
2. Page reloads.
3. Well B remains selected with the same Active/Complete status dot.

### TC-17: Verify selecting same current well is a no-op and does not reload
**Label:** Standard
**Steps**
1. Note current well A selection.
2. Re-select the same well A from the Well dropdown.
3. Observe whether a full well-change reload occurs.
**Expected Results**
1. Well A is current.
2. Same well re-selected.
3. No full well-change reload when selected id equals current well.

### TC-18: Verify Well Version and Stage stay enabled during MQTT Live Actual Treatment Schedule
**Label:** Regression
**Steps**
1. Enter Actual Treatment Schedule live MQTT mode for the current well.
2. Attempt to open Well dropdown and change wells if multiple exist.
3. Confirm Version and Stage controls remain enabled.
**Expected Results**
1. MQTT live ATS mode is active.
2. Well control remains enabled.
3. Version/Stage remain usable without Well-dropdown regression.

### TC-19: Verify Version dropdown still works after repeated Well dropdown switches
**Label:** Regression
**Steps**
1. Switch wells twice using Well dropdown.
2. Change Version on the newly selected well.
3. Confirm version load succeeds and well selection stays correct.
**Expected Results**
1. Well switches succeed; pad unchanged.
2. Version change accepted.
3. No regression in Version dropdown after Well switches.

### TC-20: Verify Reports data refreshes for newly selected well after header switch
**Label:** Regression
**Steps**
1. From well A switch to well B using header Well dropdown.
2. Open Reports for current context.
3. Confirm report content belongs to well B.
**Expected Results**
1. Well B active.
2. Reports opens.
3. Report data is for well B not stale well A.

### TC-21: Verify Plots templates refresh for newly selected well after header switch
**Label:** Regression
**Steps**
1. On well A open Plots and note template context.
2. Switch to well B via Well dropdown.
3. Open Plots and verify templates/data for well B.
**Expected Results**
1. Well A plot context noted.
2. Well B loads.
3. Plots reflect well B without stale well A context.

### TC-22: Verify Material Selection and Treatment Schedule refresh after well switch
**Label:** Regression
**Steps**
1. Note Material Selection and Treatment Schedule context on well A.
2. Switch to well B via Well dropdown.
3. Re-open both modules and verify well B data.
**Expected Results**
1. Well A baselines recorded.
2. Well B loads.
3. Both modules show well B data.

### TC-23: Verify well switch clears prior stage and treatment selection state
**Label:** Regression
**Steps**
1. On well A select a non-default stage/treatment.
2. Switch to well B via Well dropdown.
3. Inspect stage/treatment selection after load.
**Expected Results**
1. Non-default stage set on well A.
2. Well B loads.
3. Prior stage/treatment selection is cleared.

### TC-24: Verify Well dropdown hidden in fullscreen plot and restored after exit
**Label:** Regression
**Steps**
1. Enter fullscreen plot view.
2. Confirm sub-menubar Well dropdown is not shown.
3. Exit fullscreen and confirm Well dropdown returns with status dots.
**Expected Results**
1. Fullscreen active.
2. Well dropdown hidden.
3. Well dropdown visible again after exit with correct status dot.

### TC-25: Verify plot popout open does not break well switch context sync
**Label:** Regression
**Steps**
1. Open a plot popout.
2. Switch wells using header Well dropdown.
3. Confirm main page well context remains consistent.
**Expected Results**
1. Popout open.
2. Well switch completes.
3. Well context stays consistent without corrupted payload sync.
