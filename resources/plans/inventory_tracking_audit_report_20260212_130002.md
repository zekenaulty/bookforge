# Inventory Tracking Audit Report ({ts})

## Purpose
Determine whether inventory tracking data is incorrect or whether lint errors are caused by workflow/state reconciliation gaps. This review cross-checks phase outputs, state files, and lint reports with exact file/line references.

## Sources Reviewed (verifiable)
- `workspace/books/criticulous_b1/draft/context/characters/artie__885370d6.state.json`
- `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc007/state_repair_patch.json`
- `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc007/lint_report.json`
- `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc005/state_repair_patch.json`
- `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc005/continuity_pack.json`
- `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc005/lint_report.json`

## Findings

### Finding 1 ? Character invariants are stale (root cause of pipeline_state_incoherent)
**Conclusion:** Inventory data in character state invariants is stale; the actual inventory arrays are correct. Lint is correctly flagging incoherence between must_stay_true (lost/dropped) and character invariants (carried/stowed). This is a workflow/state-apply issue, not a mis-tracked inventory update.

**Evidence:**
- Character invariants still list the pre-death items as carried/stowed:
  - `artie__885370d6.state.json:24-29` show the dollar bill, smartphone, and wallet as carried/stowed in pockets/hand. These are the stale entries causing incoherence.
    - `workspace/books/criticulous_b1/draft/context/characters/artie__885370d6.state.json:24-29`
- State repair explicitly removes those items in must_stay_true for later scenes:
  - `state_repair_patch.json:123-125` (scene 7) includes REMOVE lines for the same items.
    - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc007/state_repair_patch.json:123-125`
- Lint correctly reports the contradiction between must_stay_true and character invariants:
  - `lint_report.json:6-8` (scene 7) explicitly cites the mismatch (carried/stowed vs lost/dropped).
    - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc007/lint_report.json:6-8`

**Interpretation:**
- The inventory arrays are updated, but character invariants are not being purged when REMOVE lines are emitted.
- Fix needed: apply REMOVE logic to character_state.invariants (code path), not just to summary/key_facts.

---

### Finding 2 ? Inventory posture change not reflected in must_stay_true (Fizz guidebook)
**Conclusion:** The inventory update itself is correct, but must_stay_true (pre-scene continuity) wasn't updated, so lint reports a contradiction. This is a prompt/output gap in state_repair (missing must_stay_true updates for posture changes).

**Evidence:**
- State repair patch shows Fizz's guidebook **held**:
  - `state_repair_patch.json:92-93` and `:153-154` show `ITEM_guidebook` with `status: held`.
    - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc005/state_repair_patch.json:92-93`
    - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc005/state_repair_patch.json:153-154`
- Continuity pack (pre-scene must_stay_true) still lists the guidebook as **stowed in satchel**:
  - `continuity_pack.json:8-9` and `:37-38` show `inventory: CHAR_FIZZ -> The Noob's Guide to Not Dying (status=stowed, container=satchel)`.
    - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc005/continuity_pack.json:8-9`
    - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc005/continuity_pack.json:37-38`
- Lint flags the contradiction directly:
  - `lint_report.json:6-10` (scene 5) cites must_stay_true stowed vs post-state held.
    - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc005/lint_report.json:6-10`

**Interpretation:**
- Inventory update is correct; must_stay_true was not updated to reflect the new posture.
- Fix needed: prompt rule enforcing must_stay_true updates + REMOVE lines whenever inventory posture changes (repair/state_repair/write; preflight must signal posture changes clearly).

---

### Finding 3 ? Inventory updates themselves appear correct in patches
**Conclusion:** The actual inventory updates are being applied correctly in patches; errors arise from stale invariants and stale must_stay_true, not from the inventory update logic itself.

**Evidence:**
- Scene 7 state repair patch shows Artie holding Participation Trophy in inventory:
  - `state_repair_patch.json:32-33` show `ITEM_participation_trophy` with `status: held`.
    - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc007/state_repair_patch.json:32-33`
- The same scene's must_stay_true is updated to show the Participation Trophy held:
  - `state_repair_patch.json:130` shows `inventory: CHAR_ARTIE -> Participation Trophy (held, container=hand_right)`.
    - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc007/state_repair_patch.json:130`

**Interpretation:**
- The inventory update mechanics are correct; the mismatch is on invariants cleanup (Finding 1) and must_stay_true reconciliation (Finding 2).

---

## Answer to the core question
**Is inventory tracking data itself wrong?**
- **No** for the actual inventory arrays (they show the correct held/stowed state in patches).
- **Yes** for the character invariants (they are stale and still reflect pre-death items), which contaminates lint.
- **Yes** for must_stay_true posture synchronization in some scenes (Fizz guidebook case), which causes lint to flag contradictions even when inventory is correct.

## Recommended Fixes (aligned with the plan)
1. **Code fix:** Apply REMOVE logic to `character_state.invariants` (not just summary/key_facts). This removes the stale inventory invariants that are causing repeated pipeline_state_incoherent errors.
2. **Prompt fix:** Ensure state_repair/repair/write preflight consistently update must_stay_true when inventory posture changes (and issue REMOVE lines for old posture entries).
3. **Lint resolver fix:** Treat ITEM_ tokens as item_registry only (not plot_devices) to avoid false durable_slice_missing errors.

## Notes
- This audit is backed entirely by stored artifacts and line references. There is no reliance on inferred or ?best guess? interpretation.
