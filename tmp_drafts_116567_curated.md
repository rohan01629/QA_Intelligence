STORY: FracPro Live+- Minifrac- Update Closure Parameters on Dragging Closure Line
US: 116567
COUNT: 50
NOTE: Dry-run curated drafts — not uploaded to ADO
SOURCE: AC (4 Scenario blocks) + D:\Live_Plus_UAT (stub) + Minifrac scan
COMPLEXITY: complex (Rule 11 → ~50)
RULE 13 MIX: Critical 10% / Regression 30% (assigned after generation by impact)
LABELS: Critical=5 (TC-1, TC-6, TC-9, TC-12, TC-15); Regression=15 (TC-16, TC-17, TC-23, TC-24, TC-27, TC-28, TC-29, TC-33, TC-35, TC-38, TC-39, TC-40, TC-41, TC-43, TC-44)
---

## Label summary

### Critical (10% = 5)
- TC-1: Verify dragging Closure line invokes MinifracFunc command
- TC-6: Verify x for Closure drag uses same calculation logic as tangent-line right-click
- TC-9: Verify SignalR response after MinifracFunc triggers minifracParams GET
- TC-12: Verify Information Box refreshes after successful minifracParams GET
- TC-15: Verify end-to-end Closure drag synchronizes plot position, command, API, and Information Box

### Regression (30% = 15)
- TC-16: Verify successive Closure drags each run a fresh MinifracFunc → SignalR → minifracParams → Information Box cycle
- TC-17: Verify rapid successive Closure drags do not leave Information Box on an older position
- TC-23: Verify Closure drag still works after leaving and returning to Minifrac
- TC-24: Verify Closure line visual position updates during/after drag independently of Information Box timing
- TC-27: Verify Closure drag does not require plot reload to re-enable subsequent drags
- TC-28: Verify Information Box does not require page navigation to show updated Closure parameters
- TC-29: Verify only Closure drag uses this update path — unrelated plot clicks do not call MinifracFunc with y=-1
- TC-33: Verify UI: Closure line remains selectable/draggable after Information Box update
- TC-35: Verify UI: dragging Closure shows immediate line movement feedback
- TC-38: Verify regression: Entry Friction analysis still opens and functions after Minifrac Closure-drag work
- TC-39: Verify regression: existing plot command flows (e.g. step-down callCommand) still work
- TC-40: Verify regression: SignalR connection used by the app still starts for non-Minifrac features
- TC-41: Verify regression: navigating Analysis miniFrac route still reaches Minifrac screen
- TC-43: Verify edge: switching wells/treatments then dragging Closure uses new context for minifracParams
- TC-44: Verify edge: Information Box retains non-Closure fields while Closure-related fields update

### Standard (60% = 30)
- TC-2: Verify MinifracFunc is not invoked until Closure drag completes to a new position
- TC-3: Verify MinifracFunc payload y value is always -1 on Closure drag
- TC-4: Verify MinifracFunc payload y remains -1 across multiple Closure drag positions
- TC-5: Verify MinifracFunc payload x reflects the new Closure line position
- TC-7: Verify Closure-drag x calculation remains consistent when repeating the same target position
- TC-8: Verify MinifracFunc is invoked after drag ends (not only on mouse-down)
- TC-10: Verify minifracParams GET is not called before SignalR response for the drag command
- TC-11: Verify minifracParams GET retrieves updated Minifrac parameters for current context
- TC-13: Verify Information Box updates without requiring a manual plot refresh
- TC-14: Verify Information Box Closure-related fields change when Closure moves to a different pressure/time region
- TC-18: Verify behavior when SignalR response for MinifracFunc fails or times out
- TC-19: Verify behavior when minifracParams GET returns an error after SignalR success
- TC-20: Verify behavior when minifracParams GET returns empty or incomplete Closure parameters
- TC-21: Verify dragging Closure when SignalR is disconnected
- TC-22: Verify no MinifracFunc invocation when Closure line is not displayed
- TC-25: Verify dragging Closure near plot min X edge still sends valid MinifracFunc x and y=-1
- TC-26: Verify Closure dragged to plot rightmost allowed X still triggers full parameter refresh path
- TC-30: Verify MinifracFunc command name/identifier is MinifracFunc (not a different analysis Func)
- TC-31: Verify API: minifracParams is invoked via GET method
- TC-32: Verify API: minifracParams GET uses the active well/treatment context after Closure drag
- TC-34: Verify UI: Information Box layout remains usable when values update after drag
- TC-36: Verify validation: MinifracFunc x is numeric/finite for a normal Closure drag
- TC-37: Verify validation: y is exactly -1 (not 0, 1, or omitted) on Closure drag
- TC-42: Verify edge: dragging Closure by a very small delta still follows AC update path
- TC-45: Verify negative: Closure drag while minifracParams is still in-flight from prior drag
- TC-46: Verify current build gap — Minifrac Closure drag update path not implemented yet
- TC-47: Verify after implementation: first Closure drag updates Information Box without prior page refresh
- TC-48: Verify after implementation: x calculation parity sample against tangent right-click at two locations
- TC-49: Verify after implementation: y stays -1 while x changes across a drag sequence
- TC-50: Verify after implementation: successful path displays updated Closure parameters in Information Box on final drag only once settled

---

### TC-1: Verify dragging Closure line invokes MinifracFunc command
**Label:** Critical
**Steps**
1. Open Minifrac Analysis for a well/treatment with a Closure line visible on the plot.
2. Drag the Closure line to a new X position and release.
3. Capture the outbound command/request issued for the drag.
**Expected Results**
1. Minifrac plot loads with Closure line displayed.
2. Closure line moves to the new position.
3. MinifracFunc command is invoked as a result of the drag.

### TC-2: Verify MinifracFunc is not invoked until Closure drag completes to a new position
**Label:** Standard
**Steps**
1. Open Minifrac with Closure line displayed.
2. Begin dragging Closure but return it to the original position before release (or cancel if supported).
3. Observe whether MinifracFunc is invoked.
**Expected Results**
1. Closure line is available for drag.
2. Drag gesture completes without a lasting new position (or cancel).
3. Behavior remains stable; no spurious MinifracFunc for a non-change if product treats it as no-op (document actual).

### TC-3: Verify MinifracFunc payload y value is always -1 on Closure drag
**Label:** Standard
**Steps**
1. Open Minifrac with Closure line displayed.
2. Drag Closure to a new position.
3. Inspect the MinifracFunc command payload y field.
**Expected Results**
1. Plot and Closure are ready.
2. Drag completes and MinifracFunc is sent.
3. Payload y equals -1.

### TC-4: Verify MinifracFunc payload y remains -1 across multiple Closure drag positions
**Label:** Standard
**Steps**
1. Open Minifrac with Closure line displayed.
2. Drag Closure to at least three different X positions in sequence.
3. Inspect y on each MinifracFunc invocation.
**Expected Results**
1. Closure line is draggable.
2. Each drag triggers MinifracFunc.
3. Every invocation has y = -1.

### TC-5: Verify MinifracFunc payload x reflects the new Closure line position
**Label:** Standard
**Steps**
1. Open Minifrac and note the Closure line starting X.
2. Drag Closure to a clearly different X position.
3. Compare MinifracFunc payload x to the new Closure position.
**Expected Results**
1. Initial Closure X is known.
2. Closure settles at the new position.
3. Payload x matches the new Closure line position (per product coordinate calculation).

### TC-6: Verify x for Closure drag uses same calculation logic as tangent-line right-click
**Label:** Critical
**Steps**
1. On a Minifrac/related plot where tangent right-click MinifracFunc (or equivalent) exists, right-click the tangent at a known plot location and capture computed x.
2. Drag Closure so its position maps to the same plot location used for that calculation.
3. Compare Closure-drag MinifracFunc x to the tangent right-click x for the same location.
**Expected Results**
1. Tangent right-click x is captured.
2. Closure drag MinifracFunc is invoked for the matching location.
3. x values are consistent between Closure drag and tangent right-click calculation logic.

### TC-7: Verify Closure-drag x calculation remains consistent when repeating the same target position
**Label:** Standard
**Steps**
1. Drag Closure to position A and capture MinifracFunc x.
2. Move Closure away, then drag back to the same position A.
3. Compare the second MinifracFunc x to the first.
**Expected Results**
1. First x for position A is recorded.
2. Second drag to A completes.
3. Second x equals first x (deterministic calculation).

### TC-8: Verify MinifracFunc is invoked after drag ends (not only on mouse-down)
**Label:** Standard
**Steps**
1. Open Minifrac with Closure displayed.
2. Press on Closure to start drag without moving, then move to a new position and release.
3. Correlate MinifracFunc timing with drag start vs drag end.
**Expected Results**
1. Drag interaction is available.
2. Closure moves and is released at new position.
3. MinifracFunc is associated with completing the move to the new position (per AC: when user drags to a new position).

### TC-9: Verify SignalR response after MinifracFunc triggers minifracParams GET
**Label:** Critical
**Steps**
1. Open Minifrac and drag Closure to a new position so MinifracFunc is invoked.
2. Wait for the corresponding SignalR response for that command.
3. Capture the next HTTP call related to Minifrac parameters.
**Expected Results**
1. MinifracFunc is sent.
2. Matching SignalR response is received.
3. Application calls minifracParams GET API after the SignalR response.

### TC-10: Verify minifracParams GET is not called before SignalR response for the drag command
**Label:** Standard
**Steps**
1. Prepare network monitoring before dragging Closure.
2. Drag Closure to invoke MinifracFunc.
3. Observe request order: MinifracFunc → SignalR response → minifracParams GET.
**Expected Results**
1. Monitoring is active.
2. MinifracFunc is issued on drag.
3. minifracParams GET occurs after the corresponding SignalR response, not before.

### TC-11: Verify minifracParams GET retrieves updated Minifrac parameters for current context
**Label:** Standard
**Steps**
1. Drag Closure and wait for SignalR success path.
2. Inspect minifracParams GET request (well/treatment/context identifiers).
3. Inspect response payload for updated Minifrac/Closure-related parameters.
**Expected Results**
1. SignalR path completes.
2. GET targets minifracParams for the active analysis context.
3. Response contains updated Minifrac parameters.

### TC-12: Verify Information Box refreshes after successful minifracParams GET
**Label:** Critical
**Steps**
1. Note Closure-related values shown in the Information Box before drag.
2. Drag Closure so MinifracFunc → SignalR → minifracParams GET succeeds.
3. Observe the Information Box contents.
**Expected Results**
1. Pre-drag Information Box values are known.
2. API returns successfully.
3. Information Box refreshes with the latest Closure-related parameter values.

### TC-13: Verify Information Box updates without requiring a manual plot refresh
**Label:** Standard
**Steps**
1. Open Minifrac with Information Box visible; do not use an explicit plot Refresh control.
2. Drag Closure through the full update path (command → SignalR → GET).
3. Confirm Information Box shows updated values while the plot session remains open.
**Expected Results**
1. No manual plot refresh is performed.
2. Update path completes.
3. Information Box shows updated Closure-related parameters without user-initiated plot refresh.

### TC-14: Verify Information Box Closure-related fields change when Closure moves to a different pressure/time region
**Label:** Standard
**Steps**
1. Record Information Box Closure-related values at Closure position A.
2. Drag Closure to position B where analysis results are expected to differ.
3. Compare Information Box values after the update path completes.
**Expected Results**
1. Values at A are recorded.
2. Update path for B completes.
3. Displayed Closure-related parameters reflect the new selection (not stale A values).

### TC-15: Verify end-to-end Closure drag synchronizes plot position, command, API, and Information Box
**Label:** Critical
**Steps**
1. Drag Closure to a new position.
2. Confirm Closure visual position, MinifracFunc x/y, minifracParams success, and Information Box update.
3. Ensure all four remain aligned to the same Closure selection.
**Expected Results**
1. Closure is at the new position.
2. Command and API path succeed for that position.
3. Information Box matches the updated parameters for that Closure selection.

### TC-16: Verify successive Closure drags each run a fresh MinifracFunc → SignalR → minifracParams → Information Box cycle
**Label:** Regression
**Steps**
1. Drag Closure to position A and wait for Information Box update.
2. Drag Closure to position B and wait for Information Box update.
3. Confirm a distinct update cycle occurred for B (new command/API/box values).
**Expected Results**
1. Cycle for A completes.
2. Cycle for B completes.
3. B cycle uses new Closure position; Information Box shows B values.

### TC-17: Verify rapid successive Closure drags do not leave Information Box on an older position
**Label:** Regression
**Steps**
1. Rapidly drag Closure across several positions, ending at a final position F.
2. Allow in-flight SignalR/API calls to settle.
3. Compare Information Box and Closure line to position F.
**Expected Results**
1. Final Closure position is F.
2. Outstanding updates finish or resolve.
3. Information Box reflects parameters for F (not an intermediate stale drag).

### TC-18: Verify behavior when SignalR response for MinifracFunc fails or times out
**Label:** Standard
**Steps**
1. Simulate or encounter a failed/timed-out SignalR response after Closure drag MinifracFunc.
2. Observe whether minifracParams GET is called.
3. Observe Information Box and UI stability.
**Expected Results**
1. MinifracFunc was invoked.
2. minifracParams GET is not treated as success path when SignalR did not succeed (no false success refresh).
3. UI remains stable; user is not left with a silently corrupted Information Box (error handling per product).

### TC-19: Verify behavior when minifracParams GET returns an error after SignalR success
**Label:** Standard
**Steps**
1. Complete Closure drag so MinifracFunc and SignalR succeed.
2. Cause or observe minifracParams GET failure (4xx/5xx/network).
3. Check Information Box and error feedback.
**Expected Results**
1. SignalR success occurred.
2. GET fails.
3. Information Box is not shown as successfully updated with new values; UI remains usable / shows failure appropriately.

### TC-20: Verify behavior when minifracParams GET returns empty or incomplete Closure parameters
**Label:** Standard
**Steps**
1. Complete drag path through SignalR.
2. Receive a successful HTTP response with empty/missing Closure-related fields (if reproducible).
3. Observe Information Box rendering.
**Expected Results**
1. GET returns successfully at HTTP level.
2. Payload lacks expected Closure fields.
3. UI handles missing fields without crash (blank/placeholder/unchanged per product rules).

### TC-21: Verify dragging Closure when SignalR is disconnected
**Label:** Standard
**Steps**
1. Disconnect or block SignalR while Minifrac plot is open with Closure visible.
2. Drag Closure to a new position.
3. Observe command attempt, retries/errors, and Information Box.
**Expected Results**
1. SignalR is not connected.
2. Drag is attempted.
3. Update path does not falsely refresh Information Box as success; UI remains stable.

### TC-22: Verify no MinifracFunc invocation when Closure line is not displayed
**Label:** Standard
**Steps**
1. Open Minifrac/plot context without a Closure line (or before Closure is defined).
2. Attempt drag interactions on the plot area.
3. Confirm MinifracFunc is not fired for Closure-drag semantics.
**Expected Results**
1. Closure line is absent.
2. Plot remains interactive as otherwise allowed.
3. No Closure-drag MinifracFunc is invoked.

### TC-23: Verify Closure drag still works after leaving and returning to Minifrac
**Label:** Regression
**Steps**
1. Open Minifrac, confirm Closure drag update path works once.
2. Navigate away and return to Minifrac for the same well/treatment.
3. Drag Closure again and confirm MinifracFunc → SignalR → GET → Information Box.
**Expected Results**
1. Initial path works.
2. Re-entry loads Minifrac context.
3. Second session drag again updates parameters and Information Box.

### TC-24: Verify Closure line visual position updates during/after drag independently of Information Box timing
**Label:** Regression
**Steps**
1. Drag Closure to a new X.
2. Observe Closure line position immediately after release.
3. Observe Information Box before and after API completion.
**Expected Results**
1. Drag completes.
2. Closure line shows the new position on the plot.
3. Information Box updates when params arrive; plot Closure position is not stuck at old X.

### TC-25: Verify dragging Closure near plot min X edge still sends valid MinifracFunc x and y=-1
**Label:** Standard
**Steps**
1. Drag Closure near the minimum visible/allowed X of the plot.
2. Capture MinifracFunc payload.
3. Confirm update path continues if command is accepted.
**Expected Results**
1. Closure can be placed near min edge (or clamped per UI).
2. Payload has valid x for that position and y = -1.
3. UI remains stable.

### TC-26: Verify Closure dragged to plot rightmost allowed X still triggers full parameter refresh path
**Label:** Standard
**Steps**
1. Move Closure from a mid-plot position to the rightmost allowed X on the plot.
2. Confirm MinifracFunc fires, then wait for SignalR and minifracParams GET.
3. Confirm Information Box refreshes for that right-edge Closure selection.
**Expected Results**
1. Closure settles at the rightmost allowed position (or UI clamp).
2. Full command → SignalR → GET sequence runs for that position.
3. Information Box shows updated Closure-related parameters for the right-edge selection.

### TC-27: Verify Closure drag does not require plot reload to re-enable subsequent drags
**Label:** Regression
**Steps**
1. Drag Closure once through a successful update.
2. Without refreshing the page/plot, drag Closure again.
3. Confirm second MinifracFunc is invoked.
**Expected Results**
1. First update succeeds.
2. Second drag is possible in-session.
3. Second MinifracFunc fires for the new position.

### TC-28: Verify Information Box does not require page navigation to show updated Closure parameters
**Label:** Regression
**Steps**
1. Keep Minifrac and Information Box open.
2. Drag Closure and complete successful minifracParams GET.
3. Confirm updated values appear in-place in the Information Box.
**Expected Results**
1. Information Box stays open.
2. GET succeeds.
3. Updated Closure-related parameters display without navigating away.

### TC-29: Verify only Closure drag uses this update path — unrelated plot clicks do not call MinifracFunc with y=-1
**Label:** Regression
**Steps**
1. Open Minifrac with Closure displayed.
2. Click/pan elsewhere on the plot without dragging Closure.
3. Confirm MinifracFunc Closure-drag payload (x new, y=-1) is not wrongly issued.
**Expected Results**
1. Plot is interactive.
2. Non-Closure interactions occur.
3. Closure-drag MinifracFunc path is not falsely triggered.

### TC-30: Verify MinifracFunc command name/identifier is MinifracFunc (not a different analysis Func)
**Label:** Standard
**Steps**
1. Drag Closure to a new position.
2. Inspect the command name/type on the outbound request.
3. Compare against other analysis commands (e.g. step-down) if visible in traffic.
**Expected Results**
1. Drag completes.
2. Command identifier is MinifracFunc.
3. It is distinct from unrelated plot commands.

### TC-31: Verify API: minifracParams is invoked via GET method
**Label:** Standard
**Steps**
1. Complete Closure drag through SignalR success.
2. Inspect the minifracParams HTTP method.
3. Confirm it is GET.
**Expected Results**
1. SignalR success occurred.
2. HTTP call to minifracParams is observed.
3. Method is GET.

### TC-32: Verify API: minifracParams GET uses the active well/treatment context after Closure drag
**Label:** Standard
**Steps**
1. Open Minifrac for a known well/treatment.
2. Drag Closure and capture minifracParams request URL/body/query.
3. Confirm identifiers match the open well/treatment/analysis context.
**Expected Results**
1. Correct context is open.
2. GET is issued after SignalR.
3. Request is scoped to that well/treatment/analysis context.

### TC-33: Verify UI: Closure line remains selectable/draggable after Information Box update
**Label:** Regression
**Steps**
1. Drag Closure and wait for Information Box refresh.
2. Attempt another Closure drag.
3. Confirm the line remains interactive.
**Expected Results**
1. First update completes.
2. Second drag can start.
3. Closure control is not disabled after refresh.

### TC-34: Verify UI: Information Box layout remains usable when values update after drag
**Label:** Standard
**Steps**
1. Open Information Box with Closure-related parameters visible.
2. Drag Closure so values change.
3. Inspect layout overflow/clipping/readability of updated fields.
**Expected Results**
1. Box is visible pre-update.
2. Values update.
3. Box remains readable and usable (no broken layout/crash).

### TC-35: Verify UI: dragging Closure shows immediate line movement feedback
**Label:** Regression
**Steps**
1. Press and drag the Closure line slowly across the plot.
2. Observe the line while the pointer moves.
3. Release at the new position.
**Expected Results**
1. Drag starts on Closure.
2. Line tracks the drag visually.
3. Line remains at the released position.

### TC-36: Verify validation: MinifracFunc x is numeric/finite for a normal Closure drag
**Label:** Standard
**Steps**
1. Drag Closure to a normal mid-plot position.
2. Inspect MinifracFunc payload x.
3. Confirm x is a valid numeric value (not NaN/null/undefined).
**Expected Results**
1. Drag completes.
2. Payload is available.
3. x is a finite number consistent with plot coordinates.

### TC-37: Verify validation: y is exactly -1 (not 0, 1, or omitted) on Closure drag
**Label:** Standard
**Steps**
1. Drag Closure to a new position.
2. Inspect MinifracFunc payload for y.
3. Confirm exact value and presence.
**Expected Results**
1. Command is sent.
2. y field is present.
3. y is exactly -1.

### TC-38: Verify regression: Entry Friction analysis still opens and functions after Minifrac Closure-drag work
**Label:** Regression
**Steps**
1. From analysis area, open Entry Friction for a well.
2. Confirm Entry Friction loads core UI/data as before.
3. Return to Minifrac and confirm Closure drag path still works.
**Expected Results**
1. Entry Friction opens.
2. No new regression blocking Entry Friction.
3. Minifrac Closure update path still works.

### TC-39: Verify regression: existing plot command flows (e.g. step-down callCommand) still work
**Label:** Regression
**Steps**
1. Open a plots workflow that uses existing callCommand / step-down commands (if available on the build).
2. Execute a previously working command action.
3. Confirm it still succeeds independently of Minifrac Closure drag.
**Expected Results**
1. Plots command UI is available.
2. Existing command runs.
3. No regression from Minifrac Closure-drag changes.

### TC-40: Verify regression: SignalR connection used by the app still starts for non-Minifrac features
**Label:** Regression
**Steps**
1. Load Live+ so SignalR starts (app bootstrap).
2. Exercise a non-Minifrac SignalR-dependent notification/alert if available.
3. Open Minifrac and perform one Closure drag update.
**Expected Results**
1. SignalR starts on app load.
2. Non-Minifrac SignalR behavior still works.
3. Minifrac Closure path can still use SignalR for its response.

### TC-41: Verify regression: navigating Analysis miniFrac route still reaches Minifrac screen
**Label:** Regression
**Steps**
1. Navigate to Analysis miniFrac route (`miniFrac` child route).
2. Confirm Minifrac Analysis view loads.
3. Confirm Closure (when implemented) is available for drag testing.
**Expected Results**
1. Route navigation succeeds.
2. Minifrac view is shown.
3. Screen is ready for Closure interactions when feature is implemented.

### TC-42: Verify edge: dragging Closure by a very small delta still follows AC update path
**Label:** Standard
**Steps**
1. Drag Closure by a minimal visible amount to a slightly new position.
2. Check whether MinifracFunc fires with updated x and y=-1.
3. Confirm Information Box refresh path if command is accepted.
**Expected Results**
1. Small move is recognized as new position (or documented threshold).
2. If treated as new position, MinifracFunc uses new x and y=-1.
3. Update path remains stable.

### TC-43: Verify edge: switching wells/treatments then dragging Closure uses new context for minifracParams
**Label:** Regression
**Steps**
1. Complete a Closure drag update on well/treatment A.
2. Switch to well/treatment B Minifrac context.
3. Drag Closure on B and inspect minifracParams GET context.
**Expected Results**
1. A update completed.
2. B context is active.
3. GET for B uses B identifiers (not stale A).

### TC-44: Verify edge: Information Box retains non-Closure fields while Closure-related fields update
**Label:** Regression
**Steps**
1. Note any non-Closure fields in the Information Box (if present).
2. Drag Closure and complete successful parameter refresh.
3. Compare Closure vs non-Closure fields.
**Expected Results**
1. Baseline fields recorded.
2. Update completes.
3. Closure-related fields update; unrelated fields are not incorrectly wiped unless API replaces full box content by design.

### TC-45: Verify negative: Closure drag while minifracParams is still in-flight from prior drag
**Label:** Standard
**Steps**
1. Drag Closure to A; before minifracParams returns, drag to B.
2. Allow requests to finish.
3. Confirm final Information Box aligns with final Closure position B.
**Expected Results**
1. Overlapping requests occur or are queued.
2. Requests complete.
3. Final UI state matches B (no stuck A values).

### TC-46: Verify current build gap — Minifrac Closure drag update path not implemented yet
**Label:** Standard
**Steps**
1. Open Analysis miniFrac in current Live_Plus_UAT build.
2. Inspect mini-frac-analysis UI for Closure line, MinifracFunc drag wiring, Information Box update.
3. Compare to US 116567 AC.
**Expected Results**
1. Route may load stub content (`mini-frac-analysis works!`).
2. No implemented Closure-drag → MinifracFunc → SignalR → minifracParams → Information Box flow found yet.
3. Feature gap vs US 116567 is documented for implementation tracking.

### TC-47: Verify after implementation: first Closure drag updates Information Box without prior page refresh
**Label:** Standard
**Steps**
1. After implementation, open Minifrac with Closure and Information Box visible.
2. Drag Closure once to a new position.
3. Confirm full path without refreshing the browser page.
**Expected Results**
1. Feature is available.
2. MinifracFunc → SignalR → GET completes.
3. Information Box shows updated Closure parameters without page refresh.

### TC-48: Verify after implementation: x calculation parity sample against tangent right-click at two locations
**Label:** Standard
**Steps**
1. After implementation, pick two distinct plot locations L1 and L2.
2. For each location, capture x from tangent right-click logic and from Closure drag to that location.
3. Compare pairs.
**Expected Results**
1. L1 and L2 samples are collected.
2. Both interaction types produce x for each location.
3. For each location, Closure-drag x matches tangent right-click calculation logic.

### TC-49: Verify after implementation: y stays -1 while x changes across a drag sequence
**Label:** Standard
**Steps**
1. After implementation, drag Closure across a sequence of positions.
2. Collect MinifracFunc payloads.
3. Assert y and x properties across the sequence.
**Expected Results**
1. Multiple payloads collected.
2. x changes with Closure position.
3. y is -1 on every payload.

### TC-50: Verify after implementation: successful path displays updated Closure parameters in Information Box on final drag only once settled
**Label:** Standard
**Steps**
1. After implementation, drag Closure to a final position and wait for idle network.
2. Read Information Box Closure-related parameters once.
3. Confirm they match minifracParams response for that final position.
**Expected Results**
1. Network is idle after final drag.
2. Information Box values are readable.
3. Displayed values match the successful minifracParams payload for the final Closure position.
