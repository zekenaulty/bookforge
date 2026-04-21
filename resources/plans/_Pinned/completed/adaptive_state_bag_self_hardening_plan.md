# Adaptive Continuity System State Plan

## Goal
Replace the current `stats/skills` persistence path with a dynamic, durable continuity structure that preserves any high-value mechanic metadata the LLM introduces (titles, statuses, ruleset variables, class sheets, progression systems, genre-specific mechanics) without hardcoding finite fields.

This plan is implementation-ready and focuses on the exact seams exposed in `criticulous_b1` chapter 1.

## Scope
- Replace mechanic persistence design, not inventory/container design.
- Preserve all currently good prompt constraints (timeline lock, state primacy, milestone uniqueness, no-recap discipline, inventory consistency).
- Extend and harden prompt + parser + state-apply contracts across all LLM phases.
- Add deterministic normalization and recovery before any extra LLM call.

## Out of Scope
- Building a deterministic RPG simulation engine.
- Genre-specific template forks at this phase.
- Replacing existing narrative summary mechanisms.

## Evidence from Recent Run
- Scene metadata repeatedly includes mechanic payloads in patch output:
  - `workspace/books/criticulous_b1/draft/chapters/ch_001/scene_002.meta.json`
  - `workspace/books/criticulous_b1/draft/chapters/ch_001/scene_006.meta.json`
- Persisted character state remains empty for mechanic fields despite update history:
  - `workspace/books/criticulous_b1/draft/context/characters/artie__885370d6.state.json`
- Lint repeatedly reports UI values not found in state (`HP`, `Stamina`, etc.), confirming ownership/persistence failure.

## Naming and Contract (Replace, Not Extend)
### New state keys
- Character scope: `character_continuity_system_state`
- Global/book scope: `global_continuity_system_state`

### New patch keys
- Character updates: `character_continuity_system_updates`
- Global updates: `global_continuity_system_updates`

### Update item shape
- Character update item:
  - `character_id`
  - `set` (object, optional)
  - `delta` (object, optional)
  - `remove` (array of keys, optional)
  - `reason` (string, optional)
- Global update item:
  - `set` (object, optional)
  - `delta` (object, optional)
  - `remove` (array of keys, optional)
  - `reason` (string, optional)

### Design intent
- The state object is dynamic and genre-agnostic.
- It stores canonical mechanical truth that must survive scene boundaries.
- It supports LitRPG, D&D-style sheets, Isekai power systems, and future unknown mechanic families.

## Data Modeling Rules
- Do not constrain to finite mechanic family list.
- Preserve free-form nested objects for new mechanic families.
- Normalize external labels to canonical keys when possible, but retain source label metadata for traceability.
- Numeric mechanics must live in continuity system state, not invariants.
- Invariants can reference mechanic facts but are not the source of numeric truth.

## Parser and Normalization Plan (No Extra LLM Call First)
### Entry points to update
- `src/bookforge/runner.py`
  - `_extract_prose_and_patch`
  - `_coerce_*` functions
  - `_migrate_numeric_invariants`
  - `_apply_*` update functions
  - `_lint_scene` deterministic checks
- `src/bookforge/phases/plan.py` (scene-card mechanic intent fields)
- `src/bookforge/characters.py` (initial character continuity state skeleton)

### Normalization pipeline
1. Parse output as-is.
2. Normalize legacy fields into canonical update keys.
3. Repair known malformed structures locally.
4. Validate schema.
5. Only then consider LLM retry/repair.

### Legacy inputs to accept and normalize
- `character_stat_updates`
- `character_skill_updates`
- `run_stat_updates`
- `run_skill_updates`
- direct payload blocks like:
  - `stats`
  - `skills`
  - `titles`
  - future unknown keys in update object

### Canonical local rewrite behavior
- Map legacy payload into `character_continuity_system_updates[].set`.
- Map run-level legacy payload into `global_continuity_system_updates[].set`.
- Apply key alias normalization for common stat labels (`HP`, `Crit Rate`, etc.) to stable canonical keys.
- Preserve source labels under a metadata key for debugging (for example `_source_labels`).

### Set/Delta precedence
- Keep current corrected precedence: delta first, set last for authoritative final values.

## LLM Phase-by-Phase Plan
## 1) Planning Phase (`plan_scene`)
### Required prompt extension
- Add optional scene-card mechanic intent fields:
  - `continuity_system_focus` (array of mechanic domains expected in scene)
  - `ui_mechanics_expected` (array of likely UI labels)
- Keep existing scene-card structure intact.

### Definition of done
- Scene cards can carry mechanic intent guidance without forcing deterministic simulation.
- Existing planning behavior remains valid when fields are absent.

## 2) Continuity Pack Phase
### Required prompt extension
- Include mechanic snapshot for cast and global scope:
  - `cast_continuity_system_state`
  - `global_continuity_system_state`
- Add constraint language:
  - reuse existing canonical labels and values unless explicitly updated in patch.

### Definition of done
- Continuity pack always contains mechanics context for cast and global scope.
- No new mechanic labels invented when canonical labels already exist.

## 3) Write Phase
### Required prompt extension
- Replace stats/skills-specific wording with continuity-system wording.
- Require all mechanics and UI values to be sourced from or written to `character_continuity_system_updates` / `global_continuity_system_updates`.
- Require new mechanic families (for example titles, ranks, affinities) to be explicitly added to continuity updates.

### Definition of done
- Writer emits canonical continuity-system updates, not legacy stats/skills blobs.
- Dynamic mechanic additions appear in updates in the same scene they are introduced.

## 4) State Repair Phase
### Required prompt extension
- State repair is the primary reconciler for mechanic ownership.
- If prose/UI mechanics are present and patch is missing updates, generate continuity-system updates deterministically from evidence.
- For uncertain extraction, prefer conservative update plus reason note.

### Definition of done
- Missing mechanic updates are added before state apply.
- Titles and other non-stats mechanics are captured in continuity-system state.

## 5) Repair Phase
### Required prompt extension
- Repair output must preserve prose intent and emit canonical continuity update keys.
- Forbid legacy-only update output in final repaired patch.

### Definition of done
- Repair output no longer relies on deprecated stats/skills keys.

## 6) Lint Phase
### Deterministic checks to extend
- UI ownership checks read from continuity-system state (cast-aware + global fallback).
- Detect unowned mechanic labels in prose/UI.
- Detect mismatch between displayed values and candidate continuity values.
- Detect newly introduced mechanic families with no matching update.

### Definition of done
- Lint catches mechanic ownership and mismatch errors using new state paths.
- Multi-character scenes avoid false warnings from first-character assumptions.

## Prompt Preservation Strategy
Keep unchanged:
- Timeline Lock
- State primacy
- Milestone uniqueness
- Inventory/location consistency
- Output contract strictness
- No recap/opening discipline

Replace only:
- `stats/skills` references in prompt text and examples
- patch key names tied to legacy mechanic updates

Extend:
- examples for dynamic mechanic families across multiple genres
- ownership language for unknown future mechanic families

## Prompt Files to Update
- `resources/prompt_templates/system_base.md`
- `resources/prompt_templates/write.md`
- `resources/prompt_templates/state_repair.md`
- `resources/prompt_templates/repair.md`
- `resources/prompt_templates/lint.md`
- `resources/prompt_templates/continuity_pack.md`
- `resources/prompt_templates/plan.md`

## Schema Plan
### state schema
- add `character_continuity_system_state` to character state artifacts
- add `global_continuity_system_state` to book state
- deprecate direct `stats`/`skills` as compatibility mirrors during migration window

### patch schema
- add canonical update keys:
  - `character_continuity_system_updates`
  - `global_continuity_system_updates`
- keep legacy keys accepted temporarily for compatibility

## Apply/Persist Plan
- Apply canonical continuity updates in state apply path before summary merge where needed for lint coherence.
- Persist character continuity system state in per-character state files every scene.
- Persist global continuity system state in `state.json` every scene.
- Maintain compatibility mirrors for legacy readers during transition, then remove in a later cleanup story.

## Migration and Backfill Plan
- Add migration utility to backfill current workspaces:
  - lift `stats`/`skills` (if present) into `character_continuity_system_state`
  - infer and migrate titles/effects from known invariant patterns where safe
- Add idempotent migration marker in state to prevent repeated rewrites.

## Deterministic Recovery (Before LLM Retry)
When patch is malformed but parseable:
- Normalize legacy keys to canonical updates.
- Normalize scalar/list/object variants into expected shapes.
- Salvage mechanic payload from known locations (`state_patch`, `character_updates`, invariants) into canonical updates.
- Re-run schema validation.
- Retry LLM only if normalization cannot produce valid canonical patch.

## Edge Cases to Handle Explicitly
- Character updates with missing `character_id` but single cast scene.
- Mixed casing and punctuation in mechanic labels (`Critical Hit Rate`, `crit-rate`, `CRIT RATE`).
- `%` values and ratio values (`HP: 1/1`) represented as strings, ints, or nested objects.
- Same mechanic present for multiple cast members in one scene.
- New family introduced only in prose and not UI.
- Titles/ranks introduced in dialogue lines without explicit bracket UI.
- Legacy patch shape appears after migration (must still normalize).
- Scene repair output includes both legacy and canonical keys (canonical must win).

## Test Plan
### Unit tests
- patch normalization from every legacy shape to canonical continuity updates
- apply precedence and nested updates
- dynamic family ingestion (`titles`, `statuses`, custom keys)
- lint ownership and mismatch checks against new continuity paths
- deterministic salvage from malformed patch

### Integration tests
- full scene pipeline where writer outputs legacy keys, normalizer persists canonical continuity state
- full scene pipeline with new mechanic family introduced mid-run and retained in next scene
- chapter run regression for `criticulous_b1` sample conditions

### Regression tests
- ensure existing invariant and inventory guards still behave unchanged
- ensure no loss of existing prompt quality constraints

## Rollout Stories
## Story A: Contracts and schema
- Introduce new keys and canonical patch format.
- Add compatibility acceptance for legacy keys.
- DoD: schemas validate both canonical and legacy-input pathways.

## Story B: Parser/normalizer and apply path
- Implement canonical normalization and deterministic salvage.
- Persist new continuity system state keys.
- DoD: no state loss when legacy or mixed payload appears.

## Story C: Prompt migration (targeted)
- Replace only stats/skills-specific wording and examples.
- Add dynamic family examples for LitRPG, D&D, Isekai, Fantasy.
- DoD: prompts preserve prior quality constraints and emit canonical updates.

## Story D: Lint and state repair hardening
- Align lint checks and state repair to canonical continuity state.
- Add strict/warn modes for mechanic ownership.
- DoD: repeated unowned mechanic warnings disappear for valid updates.

## Story E: Migration and workspace backfill
- Backfill existing states and verify chapter rerun behavior.
- DoD: migrated books carry mechanics across scenes without manual patching.

## Acceptance Criteria (System-Level)
- Mechanic data introduced in scene prose/UI is persisted in character/global continuity state the same scene.
- Subsequent scenes receive and reuse persisted mechanic data without reinvention.
- Titles and unknown mechanic families persist without schema changes.
- Lint no longer reports recurring unowned mechanic values when patch data exists.
- Parser normalization resolves legacy payloads before requesting another LLM call.

## Immediate Next Implementation Slice
1. Story A + Story B first (schema + normalizer + apply/persist).
2. Story C second (prompt update across all LLM phases).
3. Story D third (lint/state_repair alignment).
4. Story E last (migration/backfill and validation rerun).
