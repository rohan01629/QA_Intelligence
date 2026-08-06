STORY: FracPro Live+ Plots - Prepopulate Current Template Name in the Save Template Dialog for Existing Templates
US: 115589
COUNT: 50
NOTE: Dry-run curated drafts — not uploaded to ADO
SOURCE: AC (4 Scenario blocks) + D:\Live_Plus_UAT plots-option + reuseable-modal (Save Plot openFormModal currently does not patch plotName; Rename uses prepareRenamePlotModal). Minifrac tree not primary for this Plots story.
COMPLEXITY: complex (4 Scenario N → Rule 11 ~50)
CODEBASES_ANALYZED:
  - D:\Live_Plus_UAT (primary)
  - C:\Users\WalkingTree.LAPTOP-UNM23JON\Desktop\Minifrac\fracpro-agile (secondary scan)
RULE 13 MIX: Critical 10% / Regression 30%
LABELS: Critical=5 (TC-1, TC-3, TC-5, TC-6, TC-7); Regression=15 (TC-37, TC-38, TC-39, TC-40, TC-41, TC-42, TC-43, TC-17, TC-18, TC-19, TC-29, TC-30, TC-31, TC-9, TC-10)
---

## Label summary

### Critical (10% = 5)
- TC-1: Verify Save Template dialog prepopulates current name for an existing opened template
- TC-3: Verify Save without changing the prepopulated name saves the existing template successfully
- TC-5: Verify editing the prepopulated name and saving applies the updated template name
- TC-6: Verify Save with updated name still applies existing template name validation rules
- TC-7: Verify New Template Save dialog leaves Template Name blank

### Regression (30% = 15)
- TC-37: Verify Rename Plot still prepopulates current name (neighbor workflow unchanged)
- TC-38: Verify Duplicate Plot still opens with expected name handling
- TC-39: Verify Delete Plot confirmation still shows the correct current template name
- TC-40: Verify loading another template from the sidebar still works after using Save Template
- TC-41: Verify graph-config / channel settings workflows still open after Save Template changes
- TC-42: Verify Export/print or other plot toolbar actions still work after Save Template prepopulate change
- TC-43: Verify Word/report neighbor plot save flows remain unaffected
- TC-17: Verify Cancel/close on Save Template does not change the loaded template name
- TC-18: Verify reopening Save Template after Cancel still prepopulates the current existing name
- TC-19: Verify switching from template A to template B updates the prepopulated Save name
- TC-29: Verify disabled Save Template states for invalid template contexts still apply
- TC-30: Verify after saving with updated name, subsequent Save Template prepopulates the new name
- TC-31: Verify Save without changing name does not create a second list entry with the same name
- TC-9: Verify Save Template prepopulation works for a user-defined (type 2) existing template
- TC-10: Verify Save Template prepopulation works for a Pad/company (type 3) existing template when Save is available

### Standard (60% = 30)
- TC-2: Verify prepopulated name matches the template shown in the Plots header
- TC-4: Verify Save without name change updates template content/configuration for the same template id
- TC-8: Verify New Template blank name is not prefilled from a previously opened existing template
- TC-11: Verify clearing the prepopulated name prevents empty-name save
- TC-12: Verify restricted name 'surf prc' is rejected when editing from a prepopulated existing name
- TC-13: Verify restricted name 'btm prc' is rejected on Save Template
- TC-14: Verify restricted name 'measured data' is rejected on Save Template
- TC-15: Verify duplicate template name conflict still surfaces when renaming via Save Template
- TC-16: Verify plot name max length (50) validation still applies with prepopulated names
- TC-20: Verify whitespace-only name is not accepted when replacing a prepopulated name
- TC-21: Verify Save button remains usable when prepopulated name is left unchanged (dirty/valid path)
- TC-22: Verify UpdatePlotTemplate path is used when saving existing template with same name
- TC-23: Verify create/savePlotTemplate path is used when saving a new template with a blank-started name filled in
- TC-24: Verify UI: Save Template dialog title and name label remain clear when name is prepopulated
- TC-25: Verify UI: long existing template names display and remain editable in the Save dialog
- TC-26: Verify special characters allowed by current rules still save when editing a prepopulated name
- TC-27: Verify case differences follow existing conflict/validation rules when saving from prepopulated name
- TC-28: Verify Save Template while chart data is loading does not corrupt the prepopulated name
- TC-32: Verify edge: template name with leading/trailing spaces is trimmed per existing save logic
- TC-33: Verify edge: rapid open/close of Save Template keeps prepopulation correct
- TC-34: Verify edge: Save Template after switching wells still uses the active well’s current template name
- TC-35: Verify negative: Save Template API/update failure shows error and leaves UI recoverable
- TC-36: Verify negative: opening Save Template does not mutate template content before Save
- TC-44: Verify current build gap: Save Plot openFormModal does not yet patch current template name
- TC-45: Verify after implementation: first Save Template on existing template shows name without manual typing
- TC-46: Verify after implementation: unchanged-name Save completes Scenario 2
- TC-47: Verify after implementation: renamed Save completes Scenario 3 with validations
- TC-48: Verify after implementation: new template Save dialog name stays blank (Scenario 4)
- TC-49: Verify after implementation: Save Template prepopulation parity with Rename for the same existing template
- TC-50: Verify after implementation: end-to-end existing template open → Save Template → save → list/header stay consistent

---

### TC-1: Verify Save Template dialog prepopulates current name for an existing opened template
**Label:** Critical
**Steps**
1. Open Plots and load an existing named plot template (not a new untitled template).
2. Click the Save Template / Save Plot button.
3. Inspect the Template Name / Plot Name field in the dialog.
**Expected Results**
1. Existing template is active and its name is visible in the Plots header.
2. Save Template dialog opens.
3. Template Name field is automatically populated with the current template name.

### TC-2: Verify prepopulated name matches the template shown in the Plots header
**Label:** Standard
**Steps**
1. Open an existing template whose name is displayed in the Plots title area.
2. Open Save Template.
3. Compare the dialog name field to the header template name.
**Expected Results**
1. Header shows the current template name.
2. Dialog opens successfully.
3. Dialog name field equals the header template name exactly.

### TC-3: Verify Save without changing the prepopulated name saves the existing template successfully
**Label:** Critical
**Steps**
1. Open an existing template and open Save Template so the current name is prepopulated.
2. Do not edit the name field; click Save.
3. Confirm the template list/header after save completes.
**Expected Results**
1. Dialog shows the current template name.
2. Save completes without requiring a name re-entry.
3. Existing template is saved successfully and remains the active template under the same name.

### TC-4: Verify Save without name change updates template content/configuration for the same template id
**Label:** Standard
**Steps**
1. Open an existing template, make an allowed plot configuration change, then open Save Template.
2. Leave the prepopulated name unchanged and click Save.
3. Re-open or reload the same template and inspect the saved configuration.
**Expected Results**
1. Dialog name matches the existing template.
2. Save succeeds for that template.
3. Saved configuration reflects the change under the same template identity/name.

### TC-5: Verify editing the prepopulated name and saving applies the updated template name
**Label:** Critical
**Steps**
1. Open an existing template and open Save Template with the current name prepopulated.
2. Change the name to a new valid unique name and click Save.
3. Observe the saved template name in the UI/list.
**Expected Results**
1. Dialog opens with the original name prepopulated.
2. Edited name is accepted by the dialog.
3. Template is saved using the updated name.

### TC-6: Verify Save with updated name still applies existing template name validation rules
**Label:** Critical
**Steps**
1. Open Save Template for an existing template with name prepopulated.
2. Change the name to a value that violates an existing validation rule (e.g. empty or restricted name).
3. Attempt to Save and observe validation/error behavior.
**Expected Results**
1. Dialog shows the current name initially.
2. Invalid edited name is entered.
3. Existing template name validation rules prevent a successful invalid save (error/disabled Save as designed).

### TC-7: Verify New Template Save dialog leaves Template Name blank
**Label:** Critical
**Steps**
1. Start creating a new template / untitled plot context (no existing named template loaded).
2. Open the Save Template dialog.
3. Inspect the Template Name field.
**Expected Results**
1. New-template context is active.
2. Save Template dialog opens.
3. Template Name field remains blank (current new-template behavior).

### TC-8: Verify New Template blank name is not prefilled from a previously opened existing template
**Label:** Standard
**Steps**
1. Open an existing named template, then navigate to a new/untitled template context.
2. Open Save Template.
3. Inspect the name field.
**Expected Results**
1. New/untitled context is active.
2. Dialog opens.
3. Name field is blank and does not retain the previous existing template name.

### TC-9: Verify Save Template prepopulation works for a user-defined (type 2) existing template
**Label:** Regression
**Steps**
1. Open an existing user-defined plot template.
2. Click Save Template.
3. Check the name field value.
**Expected Results**
1. User-defined template loads.
2. Dialog opens.
3. Name field is prepopulated with that user-defined template name.

### TC-10: Verify Save Template prepopulation works for a Pad/company (type 3) existing template when Save is available
**Label:** Regression
**Steps**
1. Open an existing Pad/company plot template where Save Template is enabled.
2. Open Save Template.
3. Inspect the name field and pad-related checkbox state if shown.
**Expected Results**
1. Pad template context loads and Save is available.
2. Dialog opens.
3. Name field is prepopulated with the current Pad template name.

### TC-11: Verify clearing the prepopulated name prevents empty-name save
**Label:** Standard
**Steps**
1. Open Save Template for an existing template with name prepopulated.
2. Clear the name field completely.
3. Attempt to Save.
**Expected Results**
1. Name was prepopulated.
2. Name field is empty.
3. Save is blocked or fails validation; empty plot/template name is not accepted.

### TC-12: Verify restricted name 'surf prc' is rejected when editing from a prepopulated existing name
**Label:** Standard
**Steps**
1. Open Save Template for an existing template.
2. Replace the prepopulated name with 'surf prc' and click Save.
3. Observe error/toast messaging.
**Expected Results**
1. Dialog opened with original name.
2. Restricted name is entered.
3. Save is rejected with the existing restricted-name error behavior.

### TC-13: Verify restricted name 'btm prc' is rejected on Save Template
**Label:** Standard
**Steps**
1. Open Save Template for an existing template.
2. Change the name to 'btm prc' and attempt Save.
3. Observe validation/error handling.
**Expected Results**
1. Dialog is open.
2. Restricted name is submitted.
3. Save is rejected per existing restricted-name rules.

### TC-14: Verify restricted name 'measured data' is rejected on Save Template
**Label:** Standard
**Steps**
1. Open Save Template for an existing template.
2. Change the name to 'measured data' and attempt Save.
3. Observe validation/error handling.
**Expected Results**
1. Dialog is open.
2. Restricted name is submitted.
3. Save is rejected per existing restricted-name rules.

### TC-15: Verify duplicate template name conflict still surfaces when renaming via Save Template
**Label:** Standard
**Steps**
1. Open existing template A and open Save Template (name A prepopulated).
2. Change the name to an existing different template B name and attempt Save.
3. Observe conflict messaging and whether Save is blocked.
**Expected Results**
1. Dialog shows A initially.
2. Name is changed to B.
3. Existing name-conflict validation prevents an invalid overwrite/conflict save as designed.

### TC-16: Verify plot name max length (50) validation still applies with prepopulated names
**Label:** Standard
**Steps**
1. Open Save Template for an existing template.
2. Edit the name to exceed the 50-character limit (or paste beyond max).
3. Attempt Save / observe inline limit feedback.
**Expected Results**
1. Dialog opens with current name.
2. Over-limit input is attempted.
3. Existing max-length validation/limit feedback prevents invalid save.

### TC-17: Verify Cancel/close on Save Template does not change the loaded template name
**Label:** Regression
**Steps**
1. Open an existing template and open Save Template with prepopulated name.
2. Optionally edit the name, then Cancel/close the dialog without Save.
3. Confirm the active template name in Plots.
**Expected Results**
1. Dialog shows prepopulated name.
2. Dialog is dismissed without Save.
3. Active template name/content remains unchanged.

### TC-18: Verify reopening Save Template after Cancel still prepopulates the current existing name
**Label:** Regression
**Steps**
1. Open Save Template for an existing template, Cancel without saving.
2. Open Save Template again.
3. Inspect the name field.
**Expected Results**
1. First dialog is cancelled.
2. Second dialog opens.
3. Name field is again prepopulated with the current existing template name.

### TC-19: Verify switching from template A to template B updates the prepopulated Save name
**Label:** Regression
**Steps**
1. Open existing template A, open Save Template, note prepopulated name A, then close.
2. Switch to existing template B and open Save Template.
3. Inspect the name field.
**Expected Results**
1. A was prepopulated correctly on first open.
2. B becomes the active template.
3. Dialog for B shows B’s name (not stale A).

### TC-20: Verify whitespace-only name is not accepted when replacing a prepopulated name
**Label:** Standard
**Steps**
1. Open Save Template for an existing template.
2. Replace the name with spaces only and attempt Save.
3. Observe validation.
**Expected Results**
1. Dialog opens.
2. Whitespace-only name is entered.
3. Save is blocked by existing non-empty name validation.

### TC-21: Verify Save button remains usable when prepopulated name is left unchanged (dirty/valid path)
**Label:** Standard
**Steps**
1. Open Save Template for an existing template with name prepopulated.
2. Without editing, evaluate whether Save can proceed for an unchanged existing name (per product rules).
3. Click Save if enabled, or document required minimal interaction if product requires dirty state.
**Expected Results**
1. Name is prepopulated.
2. Save affordance is evaluated for unchanged-name path.
3. User can complete Scenario 2 save-without-changing-name successfully (or documented UX step if dirty flag is required).

### TC-22: Verify UpdatePlotTemplate path is used when saving existing template with same name
**Label:** Standard
**Steps**
1. Open an existing template and open Save Template with matching current name.
2. Save without changing the name while monitoring network/API (Update vs create).
3. Confirm the same template is updated rather than a brand-new duplicate create when names match.
**Expected Results**
1. Existing template context is active.
2. Save is submitted with the same name.
3. Update existing template path is used (no unintended duplicate template with same name).

### TC-23: Verify create/savePlotTemplate path is used when saving a new template with a blank-started name filled in
**Label:** Standard
**Steps**
1. Open Save Template in new-template context (blank name).
2. Enter a unique valid name and Save.
3. Observe that a new template is created and appears in the list.
**Expected Results**
1. Name starts blank.
2. Valid unique name is saved.
3. New template is created successfully.

### TC-24: Verify UI: Save Template dialog title and name label remain clear when name is prepopulated
**Label:** Standard
**Steps**
1. Open Save Template for an existing template.
2. Observe dialog title and the name input label/value.
3. Confirm the prepopulated value is fully visible/editable.
**Expected Results**
1. Dialog opens.
2. Title/label are readable.
3. Prepopulated name is visible and editable without layout clipping.

### TC-25: Verify UI: long existing template names display and remain editable in the Save dialog
**Label:** Standard
**Steps**
1. Open an existing template with a long valid name (near max length).
2. Open Save Template.
3. Confirm the full name is present in the field and can be edited.
**Expected Results**
1. Long-named template is open.
2. Dialog opens.
3. Name field contains the long current name and remains editable.

### TC-26: Verify special characters allowed by current rules still save when editing a prepopulated name
**Label:** Standard
**Steps**
1. Open Save Template for an existing template.
2. Edit the name to include special characters that are currently allowed by product rules.
3. Save and confirm the new name persists.
**Expected Results**
1. Dialog opens with original name.
2. Allowed special-character name is entered.
3. Save succeeds and the updated name is shown.

### TC-27: Verify case differences follow existing conflict/validation rules when saving from prepopulated name
**Label:** Standard
**Steps**
1. Open Save Template for existing template named in mixed case.
2. Change only letter casing if product treats names case-insensitively for conflicts, or keep case if uniqueness is case-sensitive.
3. Save and observe conflict vs success per existing rules.
**Expected Results**
1. Dialog shows original name.
2. Casing-only edit is attempted.
3. Behavior matches existing case-insensitive/case-sensitive template name rules.

### TC-28: Verify Save Template while chart data is loading does not corrupt the prepopulated name
**Label:** Standard
**Steps**
1. Open an existing template; if loading indicators appear, open Save Template when the button is enabled.
2. Inspect the prepopulated name.
3. Cancel or Save only if stable.
**Expected Results**
1. Existing template context is known.
2. Dialog opens when Save is available.
3. Name field shows the correct current template name (not blank/garbage).

### TC-29: Verify disabled Save Template states for invalid template contexts still apply
**Label:** Regression
**Steps**
1. Navigate to a plot context where Save is disabled (e.g. missing name/id or restricted system plot if applicable).
2. Confirm Save Template cannot be opened incorrectly.
3. Switch to a valid existing named template and confirm Save becomes available.
**Expected Results**
1. Invalid context disables Save as before.
2. User cannot open an invalid Save path from that disabled state.
3. Valid existing template re-enables Save and prepopulates correctly.

### TC-30: Verify after saving with updated name, subsequent Save Template prepopulates the new name
**Label:** Regression
**Steps**
1. From an existing template, Save Template with an updated valid name successfully.
2. Open Save Template again on the now-current template.
3. Inspect the name field.
**Expected Results**
1. First save with new name succeeds.
2. Dialog opens again.
3. Name field is prepopulated with the newly saved name.

### TC-31: Verify Save without changing name does not create a second list entry with the same name
**Label:** Regression
**Steps**
1. Note the template list count/names for an existing template.
2. Open Save Template, leave name unchanged, Save.
3. Refresh/observe the template list.
**Expected Results**
1. Baseline list is known.
2. Same-name save succeeds.
3. No duplicate list entry is created for the same template name/id.

### TC-32: Verify edge: template name with leading/trailing spaces is trimmed per existing save logic
**Label:** Standard
**Steps**
1. Open Save Template for an existing template.
2. Edit the name to include leading/trailing spaces around a valid unique name and Save.
3. Inspect the stored/displayed name.
**Expected Results**
1. Dialog opens.
2. Spaced name is submitted.
3. Saved name follows existing trim behavior (spaces not unexpectedly preserved if product trims).

### TC-33: Verify edge: rapid open/close of Save Template keeps prepopulation correct
**Label:** Standard
**Steps**
1. On an existing template, open and close Save Template several times quickly.
2. Open it once more and leave it open.
3. Inspect the name field.
**Expected Results**
1. Multiple open/close cycles complete.
2. Final dialog is open.
3. Name remains correctly prepopulated with the current template name.

### TC-34: Verify edge: Save Template after switching wells still uses the active well’s current template name
**Label:** Standard
**Steps**
1. On well A open an existing template and confirm Save prepopulation.
2. Switch to well B, open an existing template there, open Save Template.
3. Confirm the prepopulated name belongs to well B’s active template.
**Expected Results**
1. Well A path works.
2. Well B template is active.
3. Dialog shows well B’s current template name (not well A stale name).

### TC-35: Verify negative: Save Template API/update failure shows error and leaves UI recoverable
**Label:** Standard
**Steps**
1. Open Save Template for an existing template with a valid prepopulated/edited name.
2. Cause or observe a save/update API failure.
3. Check error feedback and that the dialog/Plots UI remains usable.
**Expected Results**
1. Save is attempted.
2. Failure is surfaced (toast/log/error per product).
3. UI remains recoverable; user can retry or cancel.

### TC-36: Verify negative: opening Save Template does not mutate template content before Save
**Label:** Standard
**Steps**
1. Note current plot configuration for an existing template.
2. Open Save Template (name prepopulated) and Cancel.
3. Confirm plot configuration is unchanged.
**Expected Results**
1. Baseline configuration is known.
2. Dialog is cancelled.
3. No unintended content mutation occurred from merely opening the dialog.

### TC-37: Verify Rename Plot still prepopulates current name (neighbor workflow unchanged)
**Label:** Regression
**Steps**
1. Open an existing template.
2. Use Rename Plot (not Save Template).
3. Confirm the rename dialog name field is prepopulated.
**Expected Results**
1. Existing template is active.
2. Rename dialog opens.
3. Rename still prepopulates the current name as before.

### TC-38: Verify Duplicate Plot still opens with expected name handling
**Label:** Regression
**Steps**
1. Open an existing saved template.
2. Use Duplicate Plot.
3. Confirm duplicate dialog behavior for name/content still works.
**Expected Results**
1. Template is eligible for duplicate.
2. Duplicate dialog opens.
3. Duplicate workflow remains functional (no regression from Save Template prepopulate change).

### TC-39: Verify Delete Plot confirmation still shows the correct current template name
**Label:** Regression
**Steps**
1. Open an existing named template.
2. Initiate Delete Plot.
3. Confirm the confirmation UI references the correct template name.
**Expected Results**
1. Template is open.
2. Delete confirmation appears.
3. Displayed name matches the current template (neighbor delete workflow intact).

### TC-40: Verify loading another template from the sidebar still works after using Save Template
**Label:** Regression
**Steps**
1. Save an existing template via Save Template (same or updated name).
2. Select a different template from the Plots sidebar/list.
3. Confirm the other template loads.
**Expected Results**
1. Save completes.
2. Different template is selected.
3. Other template loads correctly (no list/navigation regression).

### TC-41: Verify graph-config / channel settings workflows still open after Save Template changes
**Label:** Regression
**Steps**
1. Open an existing template and optionally use Save Template once.
2. Open channel/settings related plot configuration UI used on Plots.
3. Confirm those dialogs still open and function.
**Expected Results**
1. Template context is available.
2. Settings/channel UI opens.
3. Neighbor plot configuration workflows remain usable.

### TC-42: Verify Export/print or other plot toolbar actions still work after Save Template prepopulate change
**Label:** Regression
**Steps**
1. Open an existing template.
2. Exercise a previously working toolbar action (export/print/download if available).
3. Open Save Template and confirm name prepopulation still works afterward.
**Expected Results**
1. Template is open.
2. Toolbar action still works.
3. Save Template still prepopulates correctly.

### TC-43: Verify Word/report neighbor plot save flows remain unaffected
**Label:** Regression
**Steps**
1. From Reports/related plot save areas if accessible in the same build, exercise an existing save flow unrelated to Plots Save Template prepopulate.
2. Return to Plots Save Template for an existing template.
3. Confirm Plots prepopulation still works.
**Expected Results**
1. Neighbor report/save path remains usable or N/A is documented if out of scope for environment.
2. User returns to Plots.
3. Plots Save Template prepopulation still works for existing templates.

### TC-44: Verify current build gap: Save Plot openFormModal does not yet patch current template name
**Label:** Standard
**Steps**
1. In Live_Plus_UAT, open an existing named template.
2. Click Save Plot and inspect whether plotName is blank vs prepopulated.
3. Compare to Rename Plot which already calls prepareRenamePlotModal with currentName.
**Expected Results**
1. Existing template is open.
2. Save Plot currently opens via openFormModal without preparing the current name (gap vs US 115589).
3. Rename path still demonstrates prepopulation pattern via prepareRenamePlotModal.

### TC-45: Verify after implementation: first Save Template on existing template shows name without manual typing
**Label:** Standard
**Steps**
1. After the story is implemented, open an existing template.
2. Open Save Template once.
3. Confirm the name field is filled before any typing.
**Expected Results**
1. Feature is available.
2. Dialog opens.
3. Current template name is present with zero typing (Scenario 1).

### TC-46: Verify after implementation: unchanged-name Save completes Scenario 2
**Label:** Standard
**Steps**
1. After implementation, open Save Template on an existing template.
2. Click Save without editing the name.
3. Confirm successful save of the existing template.
**Expected Results**
1. Name is prepopulated.
2. Save is clicked unchanged.
3. Existing template saves successfully.

### TC-47: Verify after implementation: renamed Save completes Scenario 3 with validations
**Label:** Standard
**Steps**
1. After implementation, open Save Template on an existing template.
2. Change to a valid unique name and Save; also spot-check one invalid name is still blocked.
3. Confirm updated name save and validation still apply.
**Expected Results**
1. Dialog prepopulates.
2. Valid rename save succeeds.
3. Invalid names still fail existing validation rules.

### TC-48: Verify after implementation: new template Save dialog name stays blank (Scenario 4)
**Label:** Standard
**Steps**
1. After implementation, open Save Template in new-template context.
2. Inspect the name field.
3. Optionally enter a name and save a new template.
**Expected Results**
1. New-template context is active.
2. Name field is blank on open.
3. New template can still be saved after entering a name.

### TC-49: Verify after implementation: Save Template prepopulation parity with Rename for the same existing template
**Label:** Standard
**Steps**
1. After implementation, open the same existing template.
2. Open Rename and note the prepopulated name; close.
3. Open Save Template and compare the prepopulated name.
**Expected Results**
1. Same template is active for both dialogs.
2. Rename shows current name.
3. Save Template shows the same current name.

### TC-50: Verify after implementation: end-to-end existing template open → Save Template → save → list/header stay consistent
**Label:** Standard
**Steps**
1. After implementation, open existing template T, open Save Template, save with same or updated valid name.
2. Observe header name and sidebar list entry.
3. Re-open Save Template once more.
**Expected Results**
1. Save completes.
2. Header and list show the saved name consistently.
3. Subsequent Save Template prepopulates that saved name.
