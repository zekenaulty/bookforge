# Pipeline Invariant Removal and Lint Fixes Plan (20260212_124834)

## Purpose
Stabilize the lint pipeline by eliminating verified mechanical incoherence and tightening prompt rules to ensure state patches fully reflect inventory/posture changes. This plan covers three fixes:
1) Code: apply REMOVE logic to character_state.invariants (in addition to summary/key_facts).
2) Prompt: state_repair must update must_stay_true when inventory posture changes, with REMOVE lines.
3) Lint: durable constraint resolver must treat ITEM_ ids as item_registry only (not plot_devices).

## Facts (verified in current artifacts)
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
- Prompts: state_repair and repair instructions on must_stay_true updates for inventory posture changes.
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

### Story 2 — Prompt: must_stay_true updates for inventory posture changes
**Goal**: enforce a prompt rule that any inventory posture change reflected in character_updates or inventory_alignment_updates must be mirrored in must_stay_true and must remove old invariants with REMOVE: lines.

**Tasks**
1. Update **state_repair** prompt:
   - Add explicit rule: any inventory posture change (held/stowed/container changes) must update must_stay_true and remove stale invariants using REMOVE lines.
   - Explicitly mention containers and inventory invariants (inventory + container lines).
2. Update **repair** prompt to mirror the same rule.
3. Ensure the same rule exists in book overrides (workspace/books/criticulous_b1/prompts/templates/*).
4. Verify prompt text includes JSON shape reminders (array contracts and removal syntax) to avoid schema errors.

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
   - Given equired_visible_on_page = ["ITEM_participation_trophy"], ensure resolver uses item_registry (and does not check plot_devices).

**Acceptance criteria**
- durable_slice_missing errors no longer misclassify ITEM_* as plot device.
- New tests pass.

## Cross-Checks / Validation Plan
- Use phase_history artifacts for at least one scene with known inventory posture change (e.g., ch001_sc005 or ch001_sc007) and verify:
  - state_repair_patch includes REMOVE lines
  - character state invariants are updated accordingly
  - lint no longer emits pipeline_state_incoherent for inventory items
- Verify durable constraint resolver with a unit test and real lint report on a scene that references ITEM_ in constraints.

## Prompt Locations (to update)
- esources/prompt_templates/state_repair.md
- esources/prompt_templates/repair.md
- Book overrides:
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
