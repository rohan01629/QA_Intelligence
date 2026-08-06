STORY: FracPro Live+ Plots - Prepopulate Current Template Name in the Save Template Dialog for Existing Templates
US: 115589
COUNT: 25
NOTE: Dry-run drafts — not uploaded to ADO
CODEBASE: D:\Live_Plus_QA\fracpro-agile
AC: 3 scenarios (prepopulate / unchanged-name warning / rename+validation)
RULE 13 MIX: Critical 3 / Regression 8

## Implementation notes (code vs US)
- IMPLEMENTED (QA): onSavePlotClick → prepareSavePlotModal prepopulates plotName.
- Scenario 2 timing: warning/disable after blur; Save may look enabled on open; savePlot still blocks conflict.
- Scenario 2 messaging: uses duplicate-name conflict text, not a dedicated 'unchanged name' message.
- State: QA Complete | Existing linked TCs: 0 | Fresh suite.

## Label summary

### Critical (3)
- TC-1: Verify Save Template dialog prepopulates current name for an existing user-defined template
- TC-4: Verify unchanged prepopulated name shows warning and disables Save after blur
- TC-7: Verify editing prepopulated name and saving applies the updated template name

### Regression (8)
- TC-15: Verify Rename Plot still prepopulates current name
- TC-16: Verify Cancel on Save Plot does not change the loaded template name
- TC-17: Verify reopening Save after Cancel still prepopulates current existing name
- TC-18: Verify switching from template A to template B updates prepopulated Save name
- TC-19: Verify Duplicate Plot still prepopulates name and content
- TC-20: Verify channel settings dialog still opens after Save Plot interaction
- TC-21: Verify built-in Fracpro Live+ templates keep Save toolbar disabled
- TC-22: Verify opening Save Plot does not mutate plot content before Save is clicked

### Standard
- TC-2: Verify prepopulated Save dialog name matches the Plots header template title
- TC-3: Verify Save prepopulation works for an existing Pad plot template
- TC-5: Verify Save click with unchanged name is blocked even if Save appears enabled on open
- TC-6: Verify unchanged-name path does not create a duplicate template list entry
- TC-8: Verify empty plot name is rejected when clearing a prepopulated name
- TC-9: Verify restricted name surf prc is rejected when editing from prepopulated name
- TC-10: Verify restricted name btm prc is rejected on Save Plot
- TC-11: Verify restricted name measured data is rejected on Save Plot
- TC-12: Verify duplicate existing template name conflict when renaming via Save Plot
- TC-13: Verify plot name max length 50 validation applies with prepopulated names
- TC-14: Verify whitespace-only name is rejected when replacing prepopulated name
- TC-23: Verify end-to-end save with new unique name keeps header and list consistent
- TC-24: Verify Save and Rename show the same prepopulated name for the same template
- TC-25: Verify user can save after changing prepopulated name to a new unique valid name

---

### TC-1: Verify Save Template dialog prepopulates current name for an existing user-defined template
**Label:** Critical
**Steps**
1. Open Plots and load an existing user-defined template (type 2) with a saved name.
2. Click the Save button in the plot toolbar.
3. Inspect the Plot Name field in the Save Plot dialog.
**Expected Results**
1. Existing template is active and name shows in the Plots header.
2. Save Plot dialog opens.
3. Plot Name field is automatically populated with the current template name.

### TC-2: Verify prepopulated Save dialog name matches the Plots header template title
**Label:** Standard
**Steps**
1. Load an existing named template and note the header title.
2. Open Save via the Save button.
3. Compare header title to the dialog Plot Name value.
**Expected Results**
1. Header displays the template name.
2. Dialog opens.
3. Dialog Plot Name exactly matches the header template name.

### TC-3: Verify Save prepopulation works for an existing Pad plot template
**Label:** Standard
**Steps**
1. Open an existing Pad/company plot template where Save is enabled.
2. Click Save and inspect the dialog title.
3. Inspect Plot Name and Pad Plots checkbox state.
**Expected Results**
1. Pad template loads.
2. Save Plot dialog opens.
3. Plot Name is prepopulated with the Pad template name and Pad Plots checkbox reflects type 3.

### TC-4: Verify unchanged prepopulated name shows warning and disables Save after blur
**Label:** Critical
**Steps**
1. Open Save for an existing user-defined template with prepopulated current name.
2. Do not edit the name; click or tab out of the Plot Name field (blur).
3. Observe inline warning message and Save button state.
**Expected Results**
1. Name field contains the current template name unchanged.
2. After blur, duplicate/conflict warning is displayed.
3. Save button becomes disabled after blur.

### TC-5: Verify Save click with unchanged name is blocked even if Save appears enabled on open
**Label:** Standard
**Steps**
1. Open Save for an existing template with prepopulated unchanged name.
2. Without blurring the name field, click Save immediately.
3. Observe whether save proceeds or is blocked.
**Expected Results**
1. Dialog opens with prepopulated unchanged name.
2. Save may appear enabled on open before blur.
3. Save action is blocked; no successful save toast or duplicate create.

### TC-6: Verify unchanged-name path does not create a duplicate template list entry
**Label:** Standard
**Steps**
1. Note template list count for an existing template.
2. Attempt Save with unchanged prepopulated name so conflict blocks save.
3. Refresh or reopen the plot list.
**Expected Results**
1. Baseline list count is recorded.
2. Save does not complete while name is unchanged and conflict-blocked.
3. No additional list entry appears for the same template name.

### TC-7: Verify editing prepopulated name and saving applies the updated template name
**Label:** Critical
**Steps**
1. Open Save on an existing template.
2. Change Plot Name to a new valid unique name and click Save.
3. Inspect plot list and header for the updated name.
**Expected Results**
1. Original name was prepopulated.
2. Edited name is accepted.
3. Template is saved using the updated name.

### TC-8: Verify empty plot name is rejected when clearing a prepopulated name
**Label:** Standard
**Steps**
1. Open Save on an existing template with prepopulated name.
2. Clear the Plot Name field completely and click Save.
3. Observe validation or error feedback.
**Expected Results**
1. Name was prepopulated.
2. Field is cleared.
3. Save is blocked with empty-name error; template is not saved.

### TC-9: Verify restricted name surf prc is rejected when editing from prepopulated name
**Label:** Standard
**Steps**
1. Open Save on an existing template.
2. Replace the prepopulated name with 'surf prc' and attempt Save.
3. Observe validation feedback.
**Expected Results**
1. Dialog opens with original name.
2. Restricted name is entered.
3. Save is rejected with existing restricted-name validation.

### TC-10: Verify restricted name btm prc is rejected on Save Plot
**Label:** Standard
**Steps**
1. Open Save on an existing template.
2. Change name to 'btm prc' and attempt Save.
3. Observe validation feedback.
**Expected Results**
1. Dialog is open.
2. Restricted name is submitted.
3. Save is rejected per existing rules.

### TC-11: Verify restricted name measured data is rejected on Save Plot
**Label:** Standard
**Steps**
1. Open Save on an existing template.
2. Change name to 'measured data' and attempt Save.
3. Observe validation feedback.
**Expected Results**
1. Dialog is open.
2. Restricted name is submitted.
3. Save is rejected per existing rules.

### TC-12: Verify duplicate existing template name conflict when renaming via Save Plot
**Label:** Standard
**Steps**
1. Open template A and Save with name prepopulated as A.
2. Change name to an existing different template B name and attempt Save.
3. Observe conflict validation message.
**Expected Results**
1. Dialog shows A initially.
2. Name is changed to B.
3. Conflict validation prevents invalid overwrite; Save blocked with conflict message.

### TC-13: Verify plot name max length 50 validation applies with prepopulated names
**Label:** Standard
**Steps**
1. Open Save on an existing template.
2. Edit name beyond 50 characters or paste over limit.
3. Attempt Save and observe feedback.
**Expected Results**
1. Dialog opens with current name.
2. Over-limit input is attempted.
3. Max-length validation prevents invalid save.

### TC-14: Verify whitespace-only name is rejected when replacing prepopulated name
**Label:** Standard
**Steps**
1. Open Save on an existing template.
2. Replace name with spaces only and attempt Save.
3. Observe validation feedback.
**Expected Results**
1. Dialog opens.
2. Whitespace-only name is entered.
3. Save is blocked by non-empty name validation.

### TC-15: Verify Rename Plot still prepopulates current name
**Label:** Regression
**Steps**
1. Open an existing named template.
2. Use Rename Plot from the plot menu.
3. Inspect the Plot Name field.
**Expected Results**
1. Template is active.
2. Rename Plot dialog opens.
3. Plot Name is prepopulated with the current template name.

### TC-16: Verify Cancel on Save Plot does not change the loaded template name
**Label:** Regression
**Steps**
1. Open Save on an existing template with prepopulated name.
2. Edit the name optionally, then Cancel without saving.
3. Confirm active template name unchanged.
**Expected Results**
1. Dialog shows prepopulated name.
2. Dialog closes without save.
3. Active template name and content remain unchanged.

### TC-17: Verify reopening Save after Cancel still prepopulates current existing name
**Label:** Regression
**Steps**
1. Open Save on an existing template and Cancel.
2. Open Save again on the same template.
3. Inspect Plot Name.
**Expected Results**
1. First dialog cancelled.
2. Second dialog opens.
3. Plot Name is again prepopulated with the current template name.

### TC-18: Verify switching from template A to template B updates prepopulated Save name
**Label:** Regression
**Steps**
1. Open template A, open Save, note name A, close.
2. Switch to template B and open Save.
3. Inspect Plot Name.
**Expected Results**
1. A was prepopulated on first open.
2. B is active.
3. Dialog shows B name not stale A.

### TC-19: Verify Duplicate Plot still prepopulates name and content
**Label:** Regression
**Steps**
1. Open an existing saved template.
2. Use Duplicate Plot.
3. Inspect prepopulated name and content handling.
**Expected Results**
1. Template is eligible.
2. Duplicate dialog opens.
3. Duplicate workflow prepopulates current name/content without regression.

### TC-20: Verify channel settings dialog still opens after Save Plot interaction
**Label:** Regression
**Steps**
1. Open an existing template and open Save Plot once.
2. Close Save Plot if still open.
3. Open Channel Selection from Plots toolbar.
**Expected Results**
1. Save Plot opened successfully.
2. Save Plot dialog is closed.
3. Channel settings UI opens and remains usable.

### TC-21: Verify built-in Fracpro Live+ templates keep Save toolbar disabled
**Label:** Regression
**Steps**
1. Open a built-in Live+ system plot such as Measured Data or Surf PRC.
2. Locate the Save toolbar button.
3. Attempt to click Save or confirm it is disabled.
**Expected Results**
1. System/built-in template is active.
2. Save toolbar remains disabled.
3. User cannot open Save Plot prepopulation flow from disabled Save for type 0.

### TC-22: Verify opening Save Plot does not mutate plot content before Save is clicked
**Label:** Regression
**Steps**
1. Note current plot channel/configuration state.
2. Open Save Plot with prepopulated name and Cancel.
3. Re-check plot configuration.
**Expected Results**
1. Baseline configuration recorded.
2. Dialog cancelled.
3. No unintended plot content mutation from merely opening the dialog.

### TC-23: Verify end-to-end save with new unique name keeps header and list consistent
**Label:** Standard
**Steps**
1. Open existing template T, open Save, change to a new valid unique name, Save.
2. Verify header and sidebar list.
3. Open Save again and inspect prepopulated name.
**Expected Results**
1. Save with new name succeeds.
2. Header and list show the new name consistently.
3. Subsequent Save prepopulates the newly saved name.

### TC-24: Verify Save and Rename show the same prepopulated name for the same template
**Label:** Standard
**Steps**
1. Open the same existing template.
2. Open Rename Plot and note the prepopulated name; close.
3. Open Save and compare the prepopulated name.
**Expected Results**
1. Same template context is used for both dialogs.
2. Rename shows the current template name.
3. Save shows the identical current template name.

### TC-25: Verify user can save after changing prepopulated name to a new unique valid name
**Label:** Standard
**Steps**
1. Open Save on an existing template with prepopulated name.
2. Change the name slightly to a new unique valid name and Save.
3. Confirm list and header reflect the new name.
**Expected Results**
1. Dialog opens with original name prepopulated.
2. New unique name is accepted.
3. Template saves under the updated name successfully.
