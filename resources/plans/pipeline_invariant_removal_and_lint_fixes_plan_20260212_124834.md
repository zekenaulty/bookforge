# Pipeline Invariant Removal and Lint Fixes Plan (20260212_124834)

## Purpose
Stabilize the lint pipeline by eliminating verified mechanical incoherence and tightening prompt rules to ensure state patches fully reflect inventory/posture changes. This plan covers three fixes:
1) Code: apply REMOVE logic to character_state.invariants (in addition to summary/key_facts).
2) Prompt: preflight + write + repair + state_repair must ensure inventory posture changes are reflected in must_stay_true, with REMOVE lines where appropriate.
3) Lint: durable constraint resolver must treat ITEM_ ids as item_registry only (not plot_devices).

## Facts (verified in current artifacts)
- Inventory arrays in patches are correct, but character_state.invariants are stale, causing pipeline_state_incoherent.
  - Evidence: inventory lines still present in `artie__885370d6.state.json:24-29` while REMOVE lines exist in state_repair patches (scene 7).
- must_stay_true does not always reflect posture changes (e.g., Fizz guidebook held vs stowed).
  - Evidence: `ch001_sc005/state_repair_patch.json` shows guidebook held while `continuity_pack.json` still lists it stowed; lint flags the contradiction.
- durable_slice_missing misclassified ITEM_* as plot_device (constraint resolution bug).
- Recurrent pipeline_state_incoherent errors stem from stale character invariants, not stale summary data.
  - Evidence: workspace/books/criticulous_b1/draft/context/characters/artie__*.state.json retains old inventory invariants after REMOVE lines were emitted in state_repair patches.
  - Lint reports: workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc007/lint_report.json, .../ch001_sc008/lint_report.json flag must_stay_true vs character invariants conflict.
- state_repair patches are removing stale invariants in must_stay_true but not fixing inventory-related must_stay_true when posture changes (e.g., Fizz guidebook posture). 
  - Evidence: workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc005/state_repair_patch.json has must_stay_true entries inconsistent with inventory posture.
- durable constraint resolver misclassifies ITEM_ tokens as plot devices, producing durable_slice_missing for items.
  - Evidence: workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc005/lint_report.json error refers to ITEM_* as plot device.

## Objectives
- Eliminate pipeline_state_incoherent errors caused by stale character invariants.
- Ensure must_stay_true always aligns with inventory posture after state repair.
- Correct lint constraint resolution so ITEM_* resolves only to item_registry, reducing false durable_slice_missing errors.

## Scope
### In scope
- Code: state patch apply logic for character invariants removal.
- Code: lint durable constraint resolver token classification.
- Prompts: preflight, write, repair, and state_repair instructions on must_stay_true updates for inventory posture changes.
- Target: global prompt templates + book overrides (criticulous_b1), keep them consistent.

### Out of scope
- Broad lint behavior changes beyond constraint resolver fix.
- Scene card re-authoring (unless required to validate fixes).
- Schema changes (use existing remove semantics and strings).

## Plan Overview

### Story 1 — Code: Apply REMOVE logic to character_state.invariants
**Goal**: when a patch includes REMOVE: lines in summary_update.must_stay_true, those removals also purge character_state.invariants (and any derived invariants used in lint convenience views).

**Tasks**
1. Locate the current invariant merge/apply path for character updates.
   - Likely in src/bookforge/pipeline/state_apply.py or src/bookforge/characters.py (depends on your current lift/shift refactor).
   - Identify where character_updates.invariants_add and/or existing invariants are merged.
2. Reuse the existing REMOVE parsing helper (added earlier for summary/key_facts) to strip matching invariants from character state.
   - Ensure matching uses the same normalization as summary removal (exact text match after normalization).
3. Apply removal before appending new invariants to avoid reintroducing stale entries.
4. Add a unit test verifying invariants removal in character state.
   - Example: starting invariants list contains old inventory lines; patch includes REMOVE lines; after apply, character.invariants no longer contains them.

**Acceptance criteria**
- Lint no longer produces pipeline_state_incoherent solely due to stale character invariants for the removed items.
- Tests verify invariants removal.

**Risks / Edge Cases**
- Over-removal if normalization is too aggressive. Mitigate by matching exact text + minimal normalization (as summary removal does now).
- Character invariants may contain duplicate/near-duplicate inventory lines (e.g., carried vs held for same item). Removal must drop all matching stale forms that appear in REMOVE lines.
- Ensure invariants cleanup does not remove non-inventory invariants (milestones, injuries) unless explicitly REMOVE?d.

### Story 2 — Prompt: must_stay_true updates for inventory posture changes
**Goal**: enforce a prompt rule that any inventory posture change reflected in character_updates or inventory_alignment_updates must be mirrored in must_stay_true and must remove old invariants with REMOVE: lines. Apply this across preflight + write + repair + state_repair so the rule is consistent in every phase that can introduce inventory posture changes.

**Tasks**
1. Update **state_repair** prompt:
   - Add explicit rule: any inventory posture change (held/stowed/container changes) must update must_stay_true and remove stale invariants using REMOVE lines.
   - Explicitly mention containers and inventory invariants (inventory + container lines).
2. Update **repair** prompt to mirror the same rule.
3. Update **write** prompt to require must_stay_true updates when inventory posture is changed in prose or patches.
4. Update **preflight** prompt to require a clear signal when posture is changed (e.g., notes or explicit mention) so downstream phases can reconcile must_stay_true; preflight itself cannot emit summary_update but must not silently introduce posture changes without signaling intent.
5. Add explicit inventory invariant formats to prompts (inventory + container lines) so LLM writes consistent must_stay_true entries.
6. Ensure the same rule exists in book overrides (workspace/books/criticulous_b1/prompts/templates/*).
7. Verify prompt text includes JSON shape reminders (array contracts and removal syntax) to avoid schema errors.

**Acceptance criteria**
- state_repair patches for scenes with posture changes include both new inventory must_stay_true entries and REMOVE lines for old ones.
- Lint no longer flags inventory posture contradictions when state_repair performs updates.

**Risks / Edge Cases**
- Overgrowth of must_stay_true if REMOVE is not applied consistently; mitigate by explicit REMOVE ordering rule (REMOVE before new invariant).
- Mis-specified inventory line formats; mitigate by including the exact canonical invariant formats in the prompt.

### Story 3 — Lint: ITEM_ ids should resolve only to item_registry
**Goal**: durable constraint resolver must not treat ITEM_ as plot_device identifiers.

**Tasks**
1. Find durable constraint resolver in src/bookforge/pipeline/lint/helpers.py (or current lint module after refactor).
2. Update token resolution logic:
   - If token starts with ITEM_, treat as item_registry only.
   - If token starts with DEVICE_, treat as plot_devices only.
   - If no prefix, allow lookup by display_name/alias across registries.
3. Add a unit test for durable constraint resolver:
   - Given required_visible_on_page = ["ITEM_participation_trophy"], ensure resolver uses item_registry (and does not check plot_devices).

**Acceptance criteria**
- durable_slice_missing errors no longer misclassify ITEM_* as plot device.
- New tests pass.

**Risks / Edge Cases**
- Tokens without prefixes (e.g., display_name references) must still resolve via alias lookup to avoid false missing slice errors.

## Cross-Checks / Validation Plan
- Use phase_history artifacts for at least one scene with known inventory posture change (e.g., ch001_sc005 or ch001_sc007) and verify:
  - state_repair_patch includes REMOVE lines
  - character state invariants are updated accordingly
  - lint no longer emits pipeline_state_incoherent for inventory items
  - character state invariants no longer contain stale inventory lines after apply
- Verify durable constraint resolver with a unit test and real lint report on a scene that references ITEM_ in constraints.

## Prompt Locations (to update)
- resources/prompt_templates/preflight.md
- resources/prompt_templates/write.md
- resources/prompt_templates/state_repair.md
- resources/prompt_templates/repair.md
- Book overrides:
  - workspace/books/criticulous_b1/prompts/templates/preflight.md
  - workspace/books/criticulous_b1/prompts/templates/write.md
  - workspace/books/criticulous_b1/prompts/templates/state_repair.md
  - workspace/books/criticulous_b1/prompts/templates/repair.md

## Code Locations (likely, confirm before editing)
- src/bookforge/pipeline/state_apply.py (summary removal already implemented; extend to character invariants)
- src/bookforge/characters.py (if character invariants merge happens here)
- src/bookforge/pipeline/lint/helpers.py (durable constraint resolution)

## Definition of Done
- All three stories implemented and tested.
- Lint reports for existing scene history show no pipeline_state_incoherent errors caused by stale character invariants.
- Durable constraint resolver no longer misclassifies ITEM_* as plot devices.
- Prompts updated in global + book overrides, with JSON shape guidance and REMOVE rules.

## Status Tracker
- Story 1: Not started
- Story 2: Not started
- Story 3: Not started

## Notes / Constraints
- Keep JSON schema intact (no new schema changes).
- Apply prompt changes consistently across global and book-level templates.
- Favor deterministic removal and explicit invariants over heuristic linting.
