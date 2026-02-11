# Durable Character Appearance System (DCAS) v1.1 Plan

## Purpose
Establish durable, cross-scene character appearance state that is:
- Canonical and consistent across scenes (like inventory).
- Enforced via authoritative surfaces (not prose policing).
- Updated only on durable changes.
- Available to write/lint/repair/state_repair and future art tooling.

## Guiding Principles
- Appearance is a durable character surface, not a prose preference.
- Authoritative surfaces are enforced; prose parsing is secondary.
- Atoms/marks are canonical truth; summary/art text are derived views.
- Temporary/ephemeral descriptors do not update appearance_current.
- Inventory owns wearables; appearance can reference derived attire only.
- Signature outfit is a milestone, not casual drift.
- Every phase is a key integration point; no optional shortcuts.

## Scope
### In
- Canon and runtime data model for appearance.
- Pipeline updates across planning, preflight, write, lint, repair, state_repair, apply.
- Prompt updates for consistent behavior across stages.
- History/snapshot support for appearance changes.
- Authoritative appearance surface in COMPLIANCE output.

### Out
- Full art prompt generation (scaffold only).
- Scene-level appearance simulation (no heavy NLP).

## Data Model
### Canon Base (series-level)
File: `workspace/series/<series>/canon/characters/<char>/character.json`
Add `appearance_base`:
- `summary`: writer-facing paragraph (derived view, optional)
- `atoms`: normalized traits (species, sex_presentation, age_band, height_band, build, hair_color/style, eye_color, skin_tone)
- `marks`: durable distinguishing features
- `style_notes`: tonal and visual cues
- `alias_map`: allowed synonyms for lint tolerance
- Optional `appearance_art.base_prompt`

### Runtime (book-level)
File: `workspace/books/<book>/draft/context/characters/<char>.state.json`
Add:
- `appearance_current`: durable canonical view for this book
  - `atoms` and `marks` are canonical
  - `summary` and `appearance_art` are derived views
- `appearance_history`: append-only diffs with chapter/scene
- `appearance_art` (optional scaffold): base_prompt/current_prompt/negative_prompt

### Patch Surface
Extend `character_updates` with optional `appearance_updates`:
- `appearance_updates.set`: atoms/marks/metadata changes only
- `appearance_updates.reason`: required for durable updates
- Do NOT set summary or art text directly (derived after acceptance)
- appearance_updates may only touch atoms/marks (canonical) and metadata (reason/notes)

## Authoritative Appearance Surface (Avoid Prose NLP)
Add a required COMPLIANCE block: `APPEARANCE_CHECK` for cast_present_ids.
- 4-8 tokens from atoms/marks per character
- Treated as an authoritative surface (like COMPLIANCE + STATE_PATCH)
- Lint enforcement backbone: APPEARANCE_CHECK vs appearance_current (alias-aware)
- Prose-based appearance checks are warning-only and never the primary pass/fail gate

## Pipeline Integration (Key Stages)
### 1) Initialization (fresh run)
- On book init or first cast appearance, seed `appearance_current` from `appearance_base`.
- Run a projection refresh to derive summary/art text from atoms/marks.
- Must happen before first write/lint for any character.

### 2) Preflight (scene alignment)
- Include appearance_current in preflight inputs.
- Preflight should NOT invent appearance; only verify presence/consistency.
- If missing appearance_current, create from appearance_base and log initialization.

### 3) Write
- Provide appearance_current atoms/marks + summary in prompt.
- Require COMPLIANCE: APPEARANCE_CHECK for cast_present_ids.
- Do not contradict atoms unless scene_card explicitly marks a durable appearance change.
- Allow ephemeral descriptors that do not change atoms.

### 4) Lint
- Hard fail if APPEARANCE_CHECK contradicts appearance_current (alias-aware).
- Prose-based appearance contradictions are warnings unless explicitly durable and uncorrected.
- Enforce timeline/last-occurrence rule for appearance claims.
- If timeline_scope/ontological_scope indicates non-real, do not mutate appearance; relax prose checks.

### 5) Repair / State Repair
- If lint flags appearance mismatch:
  - If scene_card includes appearance change, repair prose + add appearance_updates.
  - Otherwise repair prose to match appearance_current; do not mutate appearance.
- State repair must not invent appearance deltas; only commit when prose makes durable change explicit.

### 6) Apply / Persistence
- Apply appearance_updates into appearance_current.
- Append appearance_history with chapter/scene and reason.
- Snapshot character state as already done for inventory history.

### 7) Projection Refresh (post-acceptance)
- After acceptance, if atoms/marks changed or initialization occurred, run a projection refresh using characters model.
- Refresh summary/art text only; atoms/marks remain canonical truth.

## Scene Card Support (optional but high leverage)
Add optional `durable_appearance_changes` to scene_card:
- character_id
- change_type (scar_added, hair_cut, prosthetic, species_form_change, signature_outfit, etc.)
- notes
Lint fails if prose implies a durable change without scene_card/patch intent.

## Injury / Scar Boundary
- Temporary wounds, grime, pallor: EPHEMERAL (prose only).
- Permanent scars/tattoos/prosthetics: DURABLE (appearance marks).
- "Healed into scar" is an explicit transition: remove temporary status + add mark.

## Attire Boundary (Anti-Brittleness)
- Wearables are inventory-owned; appearance only references derived attire.
- `appearance_current.attire.mode = derived` by default.
- Promote signature outfit only via explicit milestone or scene_card durable_appearance_changes.

## Prompt Updates
Update templates to include:
- System base + book system: define appearance as durable surface + anchored authoritative check.
- Write: require APPEARANCE_CHECK; enforce atoms consistency; allow ephemeral descriptors.
- Lint: enforce APPEARANCE_CHECK; prose contradictions warning-only unless explicitly durable.
- Repair/state_repair: rules for when to update appearance_current.
- Preflight: ensure appearance_current exists; do not mutate unless explicit change.

## Schema Updates
- Update character canon schema to include appearance_base.
- Update runtime character state schema to include appearance_current/history/art.
- Update state_patch schema to allow appearance_updates under character_updates.
- Optional: update scene_card schema for durable_appearance_changes.

## Story Track
### Story A: Canon + Runtime Schema
- Add appearance_base to canon character schema + data.
- Add appearance_current/history to runtime character state schema.
Status: completed

### Story B: Initialization + Preflight Seeding
- Ensure appearance_current seeded from appearance_base on fresh run.
- Add preflight guard for missing appearance_current.
Status: completed

### Story C: Authoritative Appearance Surface
- Add APPEARANCE_CHECK to COMPLIANCE output in write/repair prompts.
- Inject appearance_current atoms/marks into context.
Status: completed

### Story D: Lint Enforcement (Authoritative)
- Hard fail if APPEARANCE_CHECK conflicts with appearance_current.
- Prose checks warning-first (alias-aware, timeline aware).
Status: completed

### Story E: Appearance Updates Apply + History
- Apply appearance_updates and append history snapshots.
Status: completed

### Story F: Projection Refresh
- After acceptance, regenerate summary/art from atoms/marks via characters model.
Status: completed

### Story G: Scene Card Durable Appearance Changes (Optional)
- Add optional durable_appearance_changes for explicit intent.
Status: pending

### Story H: Attire Boundary Enforcement
- Derived attire default; signature outfit via explicit milestone/change.
Status: pending

## Status Tracker
- [x] Story A: Canon + Runtime Schema
- [x] Story B: Initialization + Preflight Seeding
- [x] Story C: Authoritative Appearance Surface
- [x] Story D: Lint Enforcement (Authoritative)
- [x] Story E: Appearance Updates Apply + History
- [x] Story F: Projection Refresh
- [ ] Story G: Scene Card Durable Appearance Changes
- [ ] Story H: Attire Boundary Enforcement

## Definition of Done
- appearance_base exists for all canon characters in series.
- appearance_current/history exist for all cast at first scene.
- APPEARANCE_CHECK appears in write/repair outputs for cast_present_ids.
- Lint enforces APPEARANCE_CHECK vs appearance_current and ignores prose ambiguity unless durable.
- Appearance changes only committed via explicit appearance_updates.
- Projection refresh updates summary/art without changing atoms/marks.
- Attire remains inventory-owned unless explicit signature milestone.

## Notes / Integration Depth
- Any JSON shapes included in prompts must be explicitly defined with proven-valid examples (type-hint style) to prevent repeat schema failures.
- Treat every stage as a key integration point; do not assume implicit behavior.
- Cross-check for edge cases: synonyms, lighting, metaphors, transient injuries, and scene-specific grime.
- Ensure no silent drift: appearance_current must remain stable unless explicitly updated.
- Preflight must guarantee initial appearance data on fresh runs.
- Keep code organized by phase and file boundaries; do not grow `runner.py` further after the lift-and-shift refactor. New DCAS logic must live in the appropriate phase/module.





