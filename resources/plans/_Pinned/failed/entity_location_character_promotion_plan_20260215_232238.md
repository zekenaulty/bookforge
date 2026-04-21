# Entity Intake, Location Indexing, and Character Promotion Plan (20260215_232238)

## Purpose
Define the downstream writing-loop architecture for:
1. preserving and classifying LLM-created unknown data (never silent drop),
2. introducing first-class location indexing in runtime state,
3. promoting newly introduced characters into tracked state files.

This plan is grounded in current code behavior and is intended to be implemented alongside the transition hardening work.

## Locked Scope Decisions (2026-02-16)
1. Unknown-key intake/classification is the immediate high-priority implementation target.
2. Prose-driven character creation/promotion remains deferred until the dedicated character-emergence design is complete.
3. Runtime location indexing redesign remains planned, but full migration is deferred to a later implementation wave.
4. During this cycle, no silent data drop is allowed; uncertain data must be preserved and routed.
5. Dead or superseded fallback code should be removed rather than left dormant.

## Baseline Findings (Code-Verified)

### 1. Unknown data handling is inconsistent and partially lossy
1. Preflight patch sanitization keeps only fixed top-level keys (`_sanitize_preflight_patch`), dropping unknown top-level fields before apply.
   - `src/bookforge/pipeline/state_patch.py`
2. Runtime state apply merges `world_updates` keys directly into `state.world` with no key classification, provenance, or policy.
   - `src/bookforge/pipeline/state_apply.py`
3. `state_patch` and `state` schemas are permissive (`additionalProperties: true`), so malformed/unknown structures can pass schema but remain unmanaged.
   - `schemas/state_patch.schema.json`
   - `schemas/state.schema.json`

### 2. Character tracking exists but only for explicit IDs
1. Character state files are created only when `character_updates[].character_id` or `character_continuity_system_updates[].character_id` exists.
   - `src/bookforge/pipeline/state_apply.py`
2. Character index resolution is robust (`ensure_character_index`, `resolve_character_state_path`, `create_character_state_path`) but there is no emergence pipeline for prose-introduced characters without IDs.
   - `src/bookforge/characters.py`
3. Writing prompts currently prohibit new character/thread IDs.
   - `resources/prompt_templates/preflight.md`
   - `resources/prompt_templates/write.md`
   - `resources/prompt_templates/repair.md`
   - `resources/prompt_templates/state_repair.md`
   - `resources/prompt_templates/system_base.md`

### 3. Location tracking is weak in runtime
1. Runtime state uses `world.location` string only.
   - `schemas/state.schema.json`
2. Durable accessibility logic keys off `world.location` and compares string tokens to `location_ref`/`custody_ref`.
   - `src/bookforge/pipeline/durable.py`
3. Outline pipeline has a robust location registry and active registry artifact, but writing loop does not consume a runtime location registry as a first-class source.
   - `schemas/outline_location_registry.schema.json`
   - `src/bookforge/outline.py`

### 4. Outline-level ID registry validation is present
1. Outline validator enforces scene character/thread refs to top-level registries.
   - `src/bookforge/outline.py`
2. This does not guarantee runtime character state files exist for every introduced/active character scene-by-scene.

## Goals (What Must Be True After Implementation)
1. No LLM-created unknown key is silently dropped.
2. Unknown keys are routed through deterministic classification workflow and persisted with provenance.
3. Runtime location model changes are specified with a staged migration path and explicit defer markers.
4. Character emergence/promotion requirements are captured as design constraints for a later build wave.
5. Existing character tracking by explicit IDs remains stable until the emergence system is implemented.
6. Existing writing flow remains backward-compatible during migration.

## Non-Negotiable Principles
1. LLM remains primary semantic author/linter.
2. Deterministic code handles detection, routing, validation, provenance, and persistence.
3. Deterministic code does not silently discard unknown semantic data.
4. Deterministic code does not invent narrative/prose content.
5. All automatic transforms must be auditable in artifacts.

## Target Data Model

### A. Runtime world location model (state)
Add canonical runtime fields:
1. `state.world.location_id`: canonical location ID (`LOC_*`).
2. `state.world.location_label`: human-readable location label.
3. Keep `state.world.location` as compatibility alias during migration.

Resolution policy:
1. `location_id` is authoritative for logic.
2. `location_label` is display metadata.
3. `location` mirrors `location_label` until deprecation.

### B. Runtime location registry and indexes
Add runtime artifacts:
1. `draft/context/location_registry.json`
2. `draft/context/locations/index.json`
3. `draft/context/locations/occupancy_index.json`
4. `draft/context/locations/history/chNNN_scNNN_location_registry_*.json`

Location registry entry shape (runtime):
1. `location_id`
2. `display_name`
3. `aliases`
4. `parent_location_id` (optional)
5. `source` (`outline_seed` | `runtime_emergent`)
6. `introduced_at` (chapter/scene)
7. `last_seen_at` (chapter/scene)

### C. Character lifecycle model
Extend character tracking with lifecycle metadata:
1. `status`: `candidate` | `promoted`
2. `origin`: `outline` | `runtime_intro`
3. `mobility_scope`: `location_bound` | `location_independent` | `unknown`
4. `home_location_id` (optional)
5. `last_seen_location_id` (optional)

New artifacts:
1. `draft/context/characters/candidates.json`
2. `draft/context/characters/promotion_queue.json`
3. `draft/context/characters/promotion_log.json`

Implementation note:
1. This model is design-targeted in this cycle, not immediate implementation scope.
2. Current behavior (explicit ID-based tracking) stays active until the emergence design is approved.

### D. Unknown-key intake and classification ledger
New artifacts:
1. `draft/context/world_key_classification_log.json`
2. `draft/context/patch_intake_log.json`

Ledger entry fields:
1. `phase` (`preflight` | `write` | `repair` | `state_repair`)
2. `chapter`, `scene`
3. `raw_key_path`
4. `raw_value`
5. `classification` (`map_to_existing` | `store_extension` | `entity_signal` | `requires_human`)
6. `mapped_path` (if any)
7. `action_taken`
8. `timestamp`

## Workflow Changes

### 1. Unknown-key routing (no drop)
1. Detect unknown top-level and nested keys relevant to world/entity surfaces.
2. Preserve raw payload in phase artifacts.
3. Route unknowns into classifier phase/prompt.
4. Apply classifier result deterministically:
   - map to known field,
   - store under managed extension namespace,
   - enqueue for promotion,
   - or pause with actionable reason.

### 2. Runtime location indexing
Per scene apply:
1. Resolve scene location via priority:
   - `scene_card.location_end_id`,
   - explicit patch location ID (if added),
   - mapped label -> id via registry,
   - otherwise route to classifier.
2. Update `state.world.location_id`, `state.world.location_label`, compatibility `state.world.location`.
3. Update occupancy index using `scene_card.cast_present_ids`.
4. Snapshot registry/index history.

### 3. Character introduction and promotion
Per scene apply:
1. Capture explicit new-character signals from patch (new update block or classifier result).
2. Create candidate character state file and index entry if missing.
3. Attach scene/location provenance.
4. Promotion triggers:
   - explicitly requested by patch/classifier,
   - repeated appearances threshold,
   - outline introduces linkage.
5. Promotion process generates/updates canonical character profile and sets status `promoted`.

Current-cycle scope note:
1. This workflow remains deferred.
2. Immediate cycle work captures intake signals and preserves data, but does not auto-promote prose-only characters.

### 4. Outline -> runtime character consistency check
Before write for a scene:
1. For `scene_card.cast_present_ids` and `scene_card.introduces_ids`, ensure corresponding state entries exist.
2. If missing and known in outline, seed minimal candidate/promoted skeleton from outline character stub.
3. Record this as deterministic seeding, not silent failure.

## Implementation Workstreams (File-by-File)

### WS1: Unknown-key intake and classifier routing
Code:
1. `src/bookforge/pipeline/state_patch.py`
   - Replace preflight top-level unknown-key drop with intake capture + classification route.
2. `src/bookforge/pipeline/state_apply.py`
   - Add `world_updates` key classification entrypoint before merge.
3. New: `src/bookforge/pipeline/state_world_registry.py`
   - Known-key registry, classification policy, managed extension namespace helpers.
4. New: `src/bookforge/phases/world_key_classification_phase.py`
   - LLM classifier invocation + schema validation.

Prompts:
1. New: `resources/prompt_templates/world_key_classification.md`
2. New block: `resources/prompt_blocks/phase/state/world_key_classification_contract.md`

Schemas:
1. `schemas/state_patch.schema.json` (new optional block for classifier outputs if needed)
2. `schemas/state.schema.json` (add `world.extensions` container)

### WS2: Runtime location registry and indexing
Code:
1. New: `src/bookforge/memory/location_state.py`
   - ensure/load/save location registry, index, occupancy index, snapshots.
2. `src/bookforge/pipeline/state_apply.py`
   - canonical location apply and compatibility alias updates.
3. `src/bookforge/pipeline/durable.py`
   - prefer `world.location_id` in durable visibility/accessibility checks; fallback to label during migration.
4. `src/bookforge/runner.py`
   - ensure runtime location state files initialized at run start.

Schemas:
1. `schemas/state.schema.json` (add `world.location_id`, `world.location_label`).
2. New: `schemas/location_registry_runtime.schema.json` (if split from outline registry schema).

Status:
1. Deferred for this cycle except interface scaffolding needed by WS1.

### WS3: Character candidate/promotion pipeline
Code:
1. `src/bookforge/characters.py`
   - add candidate metadata support in index/state creation helpers.
2. `src/bookforge/pipeline/state_apply.py`
   - consume new `character_intake_updates` (or classifier output mapping) and create candidate states.
3. New: `src/bookforge/pipeline/character_promotion.py`
   - promotion queue processing and canonicalization.
4. `src/bookforge/pipeline/scene.py`
   - pre-scene ensure state entries for cast/introduces IDs.

Prompts:
1. `resources/prompt_templates/state_repair.md`
2. `resources/prompt_templates/write.md`
3. `resources/prompt_templates/repair.md`
   - replace blanket "do not invent new character ids" with controlled intake rule:
     - if new entity appears, emit intake payload (name/role/location/mobility scope), not silent omission.

Schemas:
1. `schemas/state_patch.schema.json`
   - add optional `character_intake_updates` block (array of objects).

Status:
1. Deferred for this cycle.
2. Only non-breaking prompt clarifications may land now; no full runtime promotion pipeline implementation yet.

### WS4: Outline/runtime consistency hooks
Code:
1. `src/bookforge/runner.py`
   - add cast/introduces runtime-state preflight consistency check.
2. `src/bookforge/pipeline/scene.py`
   - include `introduces_ids` in character-state load/ensure workflow where appropriate.

### WS5: Prompt policy realignment
Files:
1. `resources/prompt_templates/system_base.md`
2. `resources/prompt_templates/preflight.md`
3. `resources/prompt_templates/write.md`
4. `resources/prompt_templates/repair.md`
5. `resources/prompt_templates/state_repair.md`
6. mirrored book templates under `workspace/books/<book_id>/prompts/templates/*`

Required policy shift:
1. Keep "do not invent canonical IDs arbitrarily".
2. Add explicit allowed path for emergent entities via intake updates.
3. Require location IDs/labels to be coherent with runtime registry and scene card constraints.
4. Keep explicit-ID character policy in place until character-emergence workstream is activated.

### WS6: Reporting and audit
Code:
1. `src/bookforge/runner.py`
2. `src/bookforge/pipeline/run_logging.py`
3. `src/bookforge/pipeline/phase_history.py`

Add reporting counters:
1. `unknown_keys_detected`
2. `unknown_keys_classified`
3. `unknown_keys_requires_human`
4. `new_location_entries`
5. `new_character_candidates`
6. `characters_promoted`

## Migration and Backward Compatibility
1. Phase 1 (compat mode):
   - keep reading/writing `world.location` string.
   - populate `location_id/location_label` when available.
2. Phase 2:
   - durable and new checks use `location_id` first, fallback to label.
3. Phase 3:
   - enforce `location_id` presence for strict mode.

No forced destructive migration of existing state files.

## Testing Plan

### Unit tests
1. `tests/test_state_unknown_key_classification.py`
2. `tests/test_runtime_location_registry.py`
3. `tests/test_world_location_apply_policy.py`
4. `tests/test_character_candidate_creation.py`
5. `tests/test_character_promotion_queue.py`
6. `tests/test_cast_introduces_runtime_consistency.py`

### Integration tests
1. Scene run with emergent location label not in outline registry:
   - expect classifier + runtime registry insertion + stable location_id.
2. Scene run with new named character in prose patch intake:
   - expect candidate state file + index entry + provenance.
3. Resume run after emergent entities:
   - expect deterministic reuse without duplicate IDs.

### Regression checks
1. Existing writing loop with no emergent entities remains unchanged.
2. No silent unknown-key drop in preflight or apply.

## Risks and Mitigations
1. Risk: over-generation of candidate characters.
   - Mitigation: promotion thresholds + dedupe by alias/location context.
2. Risk: location ID churn from inconsistent labels.
   - Mitigation: alias table + stability key + deterministic ID generation.
3. Risk: retry churn from classifier loops.
   - Mitigation: max attempts + explicit pause reason + human override path.

## Delivery Sequence
1. WS1 unknown-key intake/classification.
2. WS5 prompt policy updates (non-breaking alignment only).
3. WS6 reporting and tests for WS1 scope.
4. WS2 runtime location registry (deferred wave).
5. WS3 character candidate/promotion (deferred wave).
6. WS4 outline/runtime consistency checks (deferred wave, after WS2/WS3).

## Done Criteria
1. Unknown key is never silently discarded.
2. Runtime state has canonical location identity and indexes.
3. Newly introduced characters are captured via intake artifacts with no silent loss (promotion pipeline deferred).
4. Prompt policy supports emergent entity intake rather than suppressing it.
5. End-to-end run remains stable and auditable.
