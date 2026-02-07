# Durable Inventory And Plot Device State Plan

## Purpose
- Eliminate inventory drift and plot-device continuity breaks across scene transitions.
- Keep the engine thin while making LLM updates authoritative through `state_patch`.
- Support both character-owned items and non-character story devices tied to threads/locations/factions.

## Problem Statement
- Current inventory state is too posture-focused and not durable enough for long-lived ownership/custody transitions.
- Scene transitions (battle -> town, travel skips, time jumps) require implicit posture normalization that cannot be inferred reliably from prose alone.
- Plot devices often belong to story state, not a single character, and need canonical tracking independent of cast presence.

## Design Principles
- Authoritative updates only: state changes come from explicit patch fields, not prose parsing heuristics.
- Stable IDs: every item/device uses persistent IDs across the full book run.
- Separation of concerns:
  - Item identity and canonical metadata.
  - Current custody/location/posture.
  - Per-scene transition rationale.
- Minimal deterministic logic: engine validates and applies; LLM decides scene-appropriate transitions.

## Canonical Model

### 1) Character Inventory State (Per Character)
- Keep character state files as the source for immediately carried/equipped/stowed items.
- Add structured fields:
  - `inventory_instances` (array of objects)
  - `inventory_posture` (array of objects)
  - `inventory_notes` (array, optional)
- Each instance tracks:
  - `item_id` (stable)
  - `item_name`
  - `quantity`
  - `owner_scope` (`character` by default)
  - `status` (`equipped|carried|stowed|cached|lost|consumed|broken`)
  - `container` (example: `hand_right`, `belt`, `backpack`, `locker_town_a`)
  - `scene_last_updated` (`chapter`, `scene`)

### 2) Global Item Registry (Book Scope)
- Add `draft/context/item_registry.json` as canonical registry for all tracked items/devices.
- Tracks both character and non-character items.
- Required fields per entry:
  - `item_id`, `name`, `type`, `owner_scope`
  - `custodian` (character id, faction id, location id, or `none`)
  - `linked_threads` (array of thread IDs)
  - `state_tags` (array: `sealed`, `active`, `hidden`, `fragmented`, etc.)
  - `last_seen` (`chapter`, `scene`, `location`)

### 3) Plot Device State (Non-Character)
- Add `draft/context/plot_devices.json` (or fold into registry with `type=plot_device`; choose one canonical path and keep it single-source).
- Devices support:
  - `device_id` (can reuse `item_id`)
  - `custody_scope` (`location|faction|thread|world|character`)
  - `custody_ref`
  - `activation_state`
  - `linked_threads`
  - `constraints` (non-numeric canonical facts)

## State Patch Contract Extensions
- Extend patch schema with explicit update blocks:
  - `inventory_alignment_updates`
  - `item_registry_updates`
  - `plot_device_updates`
- Update semantics:
  - `set` for authoritative values
  - `delta` for numeric counters where needed
  - `remove` only for explicit invalidation/deletion
- Require `reason` for transitions that are off-screen/implicit.

## Writing Loop Integration (Phase-by-Phase)

### Planning
- Scene card must include inventory/plot-device intent hints:
  - `required_items`
  - `forbidden_visible_items`
  - `device_presence`
  - `transition_type` (`continuous|time_skip|location_jump|aftermath|flashback`)
- DoD:
  - Scene card contains these fields (empty allowed).
  - No schema validation regressions.

### Preflight Alignment (Authoritative)
- Preflight is responsible for scene-start state alignment before continuity pack generation.
- Inputs:
  - current cast character states
  - item registry
  - plot device state
  - scene card + previous scene/last appearance context
- Outputs (patch-only):
  - inventory posture normalization
  - custody updates
  - plot-device visibility/placement updates
- Rules:
  - no ownership invention
  - no spontaneous item creation/deletion unless scene card or prior state permits
  - must include `reason` on implicit transition changes
- DoD:
  - chapter 1 scene 1 runs with no prior prose and still produces valid aligned inventory/device state.
  - battle -> bathhouse scenario updates hand-held weapons to stowed/cached with reason.

### Continuity Pack
- Continuity must ingest aligned inventory/device state from preflight, not re-infer from prose.
- Include compact per-scene continuity slices:
  - visible gear summary
  - hidden stowed critical gear summary
  - active plot devices in scope
- DoD:
  - continuity pack references canonical IDs and matches registry/state after preflight.

### Write
- Writer prompt receives aligned inventory and device context.
- Writer must not mutate state in prose-only manner; mutations must be mirrored in patch.
- DoD:
  - any newly mentioned item/device state change appears in patch updates.

### State Repair
- State repair validates write patch against canonical item/device state.
- Fills missing updates when prose clearly implies state mutation.
- Must prefer no-op when uncertain.
- DoD:
  - missing stow/equip/custody updates are repaired into valid patch format.

### Lint
- Add inventory/device consistency checks:
  - visible in prose but impossible by aligned posture
  - custody mismatch vs registry
  - plot device appears without canonical presence path
- Keep warnings/errors structured with high-signal messages.
- DoD:
  - catches sword-in-hand mismatch after location/time transitions.

### Repair
- Repair pass reconciles prose + canonical state and emits corrected patch.
- No freeform narrative changes unless needed for continuity correction.
- DoD:
  - rerun on failing inventory/device lint produces valid patch and pass state.

## Prompt Hardening Requirements
- Update templates: `plan.md`, `preflight.md`, `continuity_pack.md`, `write.md`, `state_repair.md`, `lint.md`, `repair.md`.
- Add explicit language:
  - “State mutation is invalid unless represented in patch fields.”
  - “For implicit scene transitions, normalize posture/custody with `reason`.”
  - “Track non-character plot devices as canonical state, not character inventory.”
- Include compact examples for:
  - battle -> town transition
  - handoff between characters
  - device stored at location but linked to thread

## Parser / Apply Hardening
- Apply-layer must accept and enforce new patch blocks.
- Reject malformed updates early with actionable validation paths.
- Preserve existing non-LLM repair helpers, but reduce heuristic mutation in favor of patch-authoritative flow.
- Keep backward compatibility for existing runs with migration shims.

## Migration Plan
- On first run after upgrade:
  - backfill `item_registry` from existing character inventories
  - map legacy inventory records to `inventory_instances` + posture
  - mark unknown fields as `unclassified` with no deletion
- DoD:
  - migration is idempotent and does not duplicate items.

## History / Debugability
- Keep per-loop snapshots before preflight alignment:
  - `draft/context/characters/history/chXXX_scYYY_<statefile>.json`
- Add equivalent snapshots for item registry and plot device state:
  - `draft/context/items/history/chXXX_scYYY_item_registry.json`
  - `draft/context/plot_devices/history/chXXX_scYYY_plot_devices.json`
- DoD:
  - every scene loop produces traceable before/after artifacts.

## Edge Cases To Cover
- Character absent for many scenes then returns.
- Item handoff in off-screen transition.
- Item consumed/broken and later referenced.
- Flashback scenes that should not mutate present timeline inventory.
- Parallel thread devices with same display name but different IDs.
- Scene retry/rerun without duplicate state mutation.

## Stories (Implementation Order)

### Story A: Canonical Item/Device Schemas
- Implement schemas + validators for inventory instances, item registry, plot devices.
- DoD:
  - schema files added, validation wired, tests green.

### Story B: Preflight Inventory/Device Alignment
- Extend preflight prompt + patch extraction/apply for new update blocks.
- DoD:
  - preflight produces valid updates in transition scenarios.

### Story C: Loop-Wide Prompt Integration
- Update all phase prompts and pass new context artifacts.
- DoD:
  - all phases receive canonical state, no missing template fields.

### Story D: Apply/Repair/Lint Hardening
- Add deterministic apply and lint rules for inventory/device consistency.
- DoD:
  - known mismatch fixtures fail before repair and pass after repair.

### Story E: Migration + History Snapshots
- Add migration + snapshots for character/item/device state.
- DoD:
  - reset/rerun workflows keep reproducible state timelines.

### Story F: End-to-End Scenario Tests
- Add scenario tests for LitRPG, fantasy, and mixed custody plot devices.
- DoD:
  - full chapter run keeps consistent state across all scenes with no unresolved inventory/device lint errors.

## Open Decisions
- Single-file unified registry vs separate `item_registry` + `plot_devices` files.
- Strictness level for implicit transition updates (`warn` first or `fail` immediately).
- Whether thread-linked device state lives primarily under thread data or item/device registry with thread references.
