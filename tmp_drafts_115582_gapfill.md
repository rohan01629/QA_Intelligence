STORY: FracPro Live+ Allow Users to Rename Proppant Entries from the Material Selection Screen
US: 115582
MODE: Gap-fill only (Rule 3) — existing linked TCs: 58
COUNT: 8 (missing only)
NOTE: Dry-run drafts — not uploaded to ADO
CODEBASE: D:\Live_Plus_QA\fracpro-agile
STATE: QA | Feature found: Rename icon → startRename('proppant') → RenameProppant command
RULE 13 (of these 8): Sanity 1 / Regression 2 / Standard 5

## Inventory
Existing 58 TCs (116143–116200) already cover: Rename option on Proppant Actions, rename success/failure, oldname/newname payload, SignalR wait, Material Selection refresh, Treatment Schedule + Material Usage dirty flags, no-command when name unchanged, validations, persistence, and adjacent-screen regression.

## Gaps (US / code vs existing titles)
- IMPLEMENTED: Rename is an Action-column **icon** that enables inline Proppant Name cell edit (not a separate modal dialog) — existing TCs say “dialog”; gap TCs align to actual UX.
- IMPLEMENTED: Operator → Rename icon disabled / startRename no-op.
- IMPLEMENTED: Placeholder name `-` / empty → rename not started.
- IMPLEMENTED: Empty new name on Save → revert, no RenameProppant.
- IMPLEMENTED: Success toast “Proppant Renamed Successfully.” + fetchProppantSelectionData refresh.
- IMPLEMENTED: No SignalR connectionId → dispatch blocked.
- GAP vs AC wording: AC says “Action menu” / “Rename dialog”; code uses rename.svg icon + inline cell edit.

## Label summary

### Critical / Sanity (1)
- Verify RenameProppant is sent with oldname and newname only after Proppant name is changed and Save

### Regression (2)
- Verify Fluid tab Add/Edit/Delete still work after a successful Proppant rename
- Verify Proppant Edit and Delete actions still work after Cancel of an in-progress rename

### Standard (5)
- Verify Operator cannot start Proppant Rename from Material Selection
- Verify Rename is not available for placeholder or empty Proppant rows
- Verify empty Proppant name on Save reverts without RenameProppant
- Verify starting Rename on another row reverts the previous unsaved rename edit
- Verify successful rename shows success toast and refreshes Proppant list

---

### Verify RenameProppant is sent with oldname and newname only after Proppant name is changed and Save
**Label:** Critical / Sanity
**is_regression:** false
**is_sanity:** true
**Steps**
1. On Material Selection → Proppant tab, click Rename on a valid Proppant row and change the Proppant Name cell.
2. Click Save and capture the RenameProppant command payload.
3. Confirm SignalR/command includes calc RenameProppant with oldname and newname.
**Expected Results**
1. Proppant Name cell becomes editable for the selected row only.
2. Save dispatches RenameProppant (not a normal proppant save) when the name changed.
3. Payload contains exact previous name as oldname and trimmed new name as newname.

### Verify Fluid tab Add/Edit/Delete still work after a successful Proppant rename
**Label:** Regression
**is_regression:** true
**is_sanity:** false
**Steps**
1. Successfully rename a Proppant and wait for Material Selection refresh.
2. Switch to the Fluid tab.
3. Exercise Add New Fluid or Edit/Delete on an existing fluid row.
**Expected Results**
1. Proppant rename completes and list refreshes.
2. Fluid tab opens normally.
3. Fluid Add/Edit/Delete actions still function with no regression from RenameProppant.

### Verify Proppant Edit and Delete actions still work after Cancel of an in-progress rename
**Label:** Regression
**is_regression:** true
**is_sanity:** false
**Steps**
1. Start Rename on a Proppant row and optionally edit the name without Save.
2. Clear/cancel rename mode (revert) so renameEdit is cleared.
3. Use Edit and Delete icons on a Proppant row.
**Expected Results**
1. Rename mode starts and name column unlocks for that row.
2. Rename mode ends and name reverts if cancelled/reverted.
3. Edit and Delete remain available and behave as before rename.

### Verify Operator cannot start Proppant Rename from Material Selection
**Label:** Standard
**is_regression:** false
**is_sanity:** false
**Steps**
1. Log in as Operator and open Material Selection → Proppant.
2. Inspect the Rename icon on a Proppant row with valid data.
3. Attempt to activate Rename.
**Expected Results**
1. Proppant tab loads in read-only Operator mode.
2. Rename icon is disabled (not-allowed / reduced opacity) with Rename (Read-only) tooltip.
3. Rename mode does not start and no RenameProppant command is sent.

### Verify Rename is not available for placeholder or empty Proppant rows
**Label:** Standard
**is_regression:** false
**is_sanity:** false
**Steps**
1. On Proppant tab locate a row with name empty or '-'.
2. Inspect the Rename icon state.
3. Attempt to start Rename on that row.
**Expected Results**
1. Placeholder/empty row is visible.
2. Rename icon is not actionable (disabled / no-data tooltip).
3. startRename does not enter rename mode for empty or '-' names.

### Verify empty Proppant name on Save reverts without RenameProppant
**Label:** Standard
**is_regression:** false
**is_sanity:** false
**Steps**
1. Start Rename on a valid Proppant and clear the Proppant Name to blank.
2. Click Save.
3. Monitor network/SignalR for RenameProppant.
**Expected Results**
1. Name cell is cleared while in rename mode.
2. Save reverts to the previous name and exits rename mode.
3. No RenameProppant command is sent.

### Verify starting Rename on another row reverts the previous unsaved rename edit
**Label:** Standard
**is_regression:** false
**is_sanity:** false
**Steps**
1. Start Rename on Proppant row A and change its name without Save.
2. Click Rename on Proppant row B.
3. Inspect row A name and which row is editable.
**Expected Results**
1. Row A is in rename edit with a modified name.
2. Starting rename on row B clears prior rename mode.
3. Row A reverts to oldName; only row B name cell is editable.

### Verify successful rename shows success toast and refreshes Proppant list
**Label:** Standard
**is_regression:** false
**is_sanity:** false
**Steps**
1. Rename a Proppant to a valid new name and Save.
2. Wait for successful SignalR RenameProppant response.
3. Observe toast and Material Selection Proppant grid.
**Expected Results**
1. RenameProppant is submitted.
2. Success toast shows Proppant Renamed Successfully.
3. Proppant list refreshes and shows the new name; Treatment Schedule and Material Usage are marked dirty.
