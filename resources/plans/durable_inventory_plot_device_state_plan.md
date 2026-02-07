# Durable Inventory And Plot Device State Plan (Refined v2)

## Purpose
- Prevent inventory and plot-device drift across scene transitions.
- Keep BookForge as a thin engine: LLM decides state, engine validates/applies deterministically.
- Make durable state authoritative through `state_patch`, not prose inference.

## Fixed Decisions
- Use explicit domain files (more files, clearer ownership):
  - `draft/context/item_registry.json`
  - `draft/context/plot_devices.json`
  - `draft/context/items/index.json` (optional)
  - `draft/context/plot_devices/index.json` (optional)
  - `draft/context/items/history/*.json`
  - `draft/context/plot_devices/history/*.json`
- Keep `linked_threads` in registry/device records.
- Keep lint semantics:
  - `warn`: advisory
  - `fail`: blocking
- Inventory/device contradictions default to `fail` + retry loop.

## Authority Precedence Matrix
- Custody truth: `item_registry` / `plot_devices`.
- Scene posture/view truth: character state inventory posture.
- Conflict rule:
  - if custody and posture disagree, custody wins.
  - preflight/repair must normalize posture to match custody unless scene card explicitly changes custody.
- Prose never overrides canonical state directly.

## Timeline Scope Policy
- Add `timeline_scope` to scene card and propagate to all phases:
  - `present|flashback|dream|simulation|hypothetical`.
- Apply behavior:
  - `present`: canonical mutations allowed.
  - non-`present`: canonical mutation forbidden by default.
  - explicit override required for allowed non-present mutation (`timeline_override=true` + reason).

## Canonical Data Model

### Character Inventory (Scene View)
- Keep per-character inventory posture data.
- Add/standardize:
  - `inventory_instances`
  - `inventory_posture`
  - `inventory_notes`
- Minimum item fields:
  - `item_id`, `item_name`, `quantity`, `owner_scope`, `status`, `container`, `scene_last_updated`.

### Item Registry (Durable Canon)
- File: `draft/context/item_registry.json`.
- Required per entry:
  - `item_id`, `name`, `type`, `owner_scope`, `custodian`, `linked_threads`, `state_tags`, `last_seen`.
- Supports nested storage refs where needed:
  - `container_ref`, `carrier_ref`, `location_ref` (optional).

### Plot Device Registry (Durable Canon)
- File: `draft/context/plot_devices.json`.
- Required per entry:
  - `device_id`, `name`, `custody_scope`, `custody_ref`, `activation_state`, `linked_threads`, `constraints`, `last_seen`.
- Intangible devices are first-class (oaths, secrets, vows, global flags).

### Hybrid Linkage (Item <-> Device)
- Prevent double-canon with explicit linkage:
  - item entry optional: `linked_device_id`
  - device entry optional: `linked_item_id`

## State Patch Contract Extensions
- Add patch blocks:
  - `inventory_alignment_updates`
  - `item_registry_updates`
  - `plot_device_updates`
  - `transfer_updates` (atomic ownership/custody transfers)
- Operation shape:
  - `set`, `delta`, `remove`, `reason`.
- `reason` required for implicit/off-screen transitions.

## Atomic Transfer Contract
- `transfer_updates` must update in one logical transaction:
  - source posture/state
  - destination posture/state
  - registry custody
- Partial transfer apply is invalid and must fail.

## Idempotent Commit Contract
- Add per-scene commit identity:
  - `scene_patch_id` (deterministic from `book/chapter/scene/phase/attempt` or explicit hash).
- Apply layer keeps a commit ledger.
- Re-apply same `scene_patch_id` => no-op.
- Prevents double decrement/duplicate mutation during retries.

## Strictness, Retry, Failure Flow
- High-confidence contradictions are blocking `fail`:
  - impossible posture vs scene context
  - custody mismatch
  - unauthorized ownership transfer
  - required-in-custody missing
- Retry sequence:
  1. state repair retry
  2. repair retry
  3. final lint
- If still failing: pause/abort scene progression with clear structured reason.

## Prompt And Context Strategy

### Canonical UI Naming Policy
- Canonical names/IDs required in authoritative UI/system blocks and patch outputs.
- Narrative prose may use aliases/synonyms.
- Lint fails only when authoritative UI labels drift from canonical names.

### Context Slicing Policy
- Never send full registries by default.
- Per scene send compact slices only:
  - cast-owned items/devices
  - required/forbidden scene references
  - recently touched canonical entries
  - thread-linked entries in scene scope

### Minified Outline Injection Policy
- Continue injecting full minified outline in system prompt where stage reasoning requires global story map.
- Required by default for:
  - `write`
  - `repair`
  - `state_repair`
  - `preflight`
- Optional for:
  - `continuity_pack` (enable when drift indicates outline-order issues)
  - `lint` (usually no, unless specific cross-scene ordering checks are needed)
- Add env toggles per phase to disable outline injection if cost/latency requires fallback.

## Full Writing Loop: Structural + Prompt Updates

### Planning
- Add scene card fields:
  - `required_in_custody`
  - `required_visible`
  - `forbidden_visible`
  - `device_presence`
  - `transition_type`
  - `timeline_scope`
- Prompt updates:
  - separate existence vs visibility semantics.

### Preflight
- Inputs:
  - cast state + item/plot registries + previous/last appearance context + minified outline.
- Outputs:
  - aligned inventory posture/custody updates + canonical reasons.
- Prompt updates:
  - explicit off-screen normalization constraints.

### Continuity Pack
- Consume post-preflight canonical state.
- Emit compact continuity slices only.
- Prompt updates:
  - reference canonical IDs, no freeform ownership invention.

### Write
- Receives aligned canonical slices + minified outline.
- Must mirror state changes in patch blocks.
- Prompt updates:
  - authoritative mutation rule reiterated.

### State Repair
- Receives prose + patch + canonical slices + minified outline.
- Completes missing canonical updates conservatively.

### Lint
- Deterministic checks only; no broad NLP extraction.
- Inventory/device checks + timeline scope + naming checks.

### Repair
- Fixes contradictions and emits corrected patch.
- Must preserve story intent while restoring canonical consistency.

### Apply/Commit
- Validates schema + authority precedence + idempotent commit.
- Applies atomically per scene.

## Parser/Apply Hardening
- Add strict validation for new patch blocks and transfer transactions.
- Keep fallback/parsing helpers only for shape normalization, not canonical inference.
- Add explicit error messages with path + expected/actual type.

## Migration Plan
- First run migration:
  - backfill item registry from existing inventories
  - backfill plot devices from continuity hints
  - mark uncertain migrated entries `unclassified`
- Idempotent migration required.

## History And Debugability
- Keep existing character snapshots.
- Add registry snapshots before preflight mutations:
  - `draft/context/items/history/chXXX_scYYY_item_registry.json`
  - `draft/context/plot_devices/history/chXXX_scYYY_plot_devices.json`
- Keep per-scene apply commit log with `scene_patch_id`.

## Reset Command Hardening
- Extend `bookforge reset-book` to clear all runtime context:
  - continuity pack/history
  - chapter summaries
  - item/plot registries + indexes + history
  - character history
  - generated scene/chapter outputs
  - runtime artifacts from preflight/state-repair
- Character reset behavior:
  - keep author/library canon
  - clear runtime per-book character state that biases next run
  - regenerate missing runtime character state at run start
- Log cleanup options:
  - `--keep-logs` (default false)
  - `--logs-scope book|all` (default `book`)
- Reset console output:
  - stage start/end
  - per-domain deletion counts
  - final summary totals

## Expanded Edge Cases
- Character absent long-term returns with stale posture.
- Off-screen transfer implied but not explicit.
- Item consumed/broken then referenced later.
- Duplicate display names with distinct IDs.
- Flashback/dream/sim scenes mutating present canon accidentally.
- Time rewind/checkpoint creates duplicate custody.
- Retry after partial apply double-mutation.
- Multi-actor transfer updated for one side only.
- Device linked to multiple threads with partial resolution.
- Missing/truncated previous scene prose at preflight time.
- Cached item in nested container (pack on horse in stable) with travel jump.

## Stories (Implementation Order)

### Story A: Schema + Canonical Files
- Add/validate schemas for new blocks and registries.
- DoD: schema validation + bootstrap files + tests pass.

### Story B: Authority + Timeline + Idempotent Apply
- Implement precedence matrix, timeline gating, and commit ledger.
- DoD: no duplicate apply on retry; non-present scenes cannot mutate canon without override.

### Story C: Preflight + Transfer Transactions
- Implement preflight output for inventory/device alignment and `transfer_updates`.
- DoD: transition fixtures and handoff fixtures apply atomically.

### Story D: Loop-Wide Prompt/Context Upgrade
- Update prompts and context payloads for all phases.
- Include minified outline injection per policy.
- DoD: all phase templates and payload builders updated; no missing fields.

### Story E: Lint/Repair Blocking Pipeline
- Add deterministic contradiction checks, UI naming checks, and retry flow.
- DoD: known contradictions block and resolve or pause with clear reasons.

### Story F: Migration + History + Reset
- Implement migration, snapshots, and reset command upgrades.
- DoD: reset returns clean post-outline baseline; snapshots/logs are traceable.

### Story G: End-to-End Regression Suite
- Add chapter-level runs for LitRPG/fantasy/mixed thread-device custody.
- DoD: chapter runs complete without unresolved blocking continuity failures.