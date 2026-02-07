# Durable Inventory And Plot Device State Plan (Refined v3)

## Purpose
- Prevent long-run inventory and plot-device continuity drift without turning BookForge into a simulation engine.
- Keep the current design principle: LLM proposes state, engine validates/apply atomically, prose parsing only detects/escalates.
- Make durable state explicit and auditable, including off-screen transitions such as "stowed at inn".

## In-Scope
- Inventory posture and custody continuity.
- Physical and intangible plot-device continuity.
- Retry-safe/idempotent apply behavior.
- Full writing loop integration: planning, preflight, continuity, write, state repair, lint, repair, apply/commit, reset.

## Out-Of-Scope
- Full RPG combat/stat simulation.
- Deterministic prose understanding as primary truth.
- Broad NLP extraction of inventory facts from prose.

## Fixed Architecture Decisions
- Prefer explicit domain files over overloaded monoliths.
- Canonical files:
  - `draft/context/item_registry.json`
  - `draft/context/plot_devices.json`
  - `draft/context/items/index.json` (optional)
  - `draft/context/plot_devices/index.json` (optional)
  - `draft/context/items/history/*.json`
  - `draft/context/plot_devices/history/*.json`
- Keep thread linkage in canonical entries (`linked_threads`).
- Lint semantics remain:
  - `warn` = advisory
  - `fail` = blocking and enters retry flow
- Inventory/device contradictions default to blocking `fail`.

## Operational Semantics (Authoritative)

### 1) Authority Boundary And Conflict Precedence
- Canonical custody truth:
  - `item_registry` for items
  - `plot_devices` for devices
- Scene posture/view truth:
  - character inventory/posture in character state file
- Conflict rule:
  - if custody and posture disagree, custody wins
  - preflight/state repair/repair must normalize posture toward custody unless scene card or patch explicitly changes custody
- Prose-only statements never mutate canonical state.

### 2) State Mutation Channels (No Silent Mutations)
- Valid mutation channels:
  - scene card intent (planning output)
  - patch blocks from `preflight`, `write`, `state_repair`, `repair`
- Invalid mutation channel:
  - direct prose implication without patch representation
- Blocking condition:
  - prose claims handoff/consumption/breakage while patch omits required canonical updates.

### 3) Deletion/Tombstone Policy
- Durable entries are not hard-deleted by default.
- `remove` for durable items/devices is interpreted as tombstone transition unless explicitly ephemeral.
- Tombstone minimum fields:
  - `state_tags` includes one of `destroyed|consumed|lost|retired`
  - `last_seen`
  - `resolution_note` (optional but recommended)
- Hard delete allowed only for:
  - explicitly ephemeral runtime artifacts
  - migration cleanup under deterministic mapping rules.

### 4) Transfer Semantics (Atomic + Closed-World)
- Add `transfer_updates` block for ownership/custody transfer.
- One transfer must update in one atomic apply unit:
  - source posture/state
  - destination posture/state
  - registry custody
- Partial transfer apply => invalid (`fail`) and no partial commit.

### 5) Stack And Instance Identity Rules
- Decide and enforce stack identity model:
  - unique items: single `item_id`, quantity usually `1`
  - fungible stacks: same `item_id` with `quantity` deltas OR split into `inventory_instance_id`
- For split transfers, patch must express source and destination quantities explicitly.
- Invalid state example to block:
  - same unique `item_id` simultaneously marked as carried by two characters.

### 6) Timeline Scope Gating
- Add `timeline_scope` to scene card and per-phase context:
  - `present|flashback|dream|simulation|hypothetical`
- Canonical apply policy:
  - `present`: canonical item/device mutations allowed
  - non-`present`: canonical physical custody mutation blocked by default
- Allowed non-present mutation subset (controlled):
  - knowledge-like intangible device updates (for example secret known_by updates)
  - linkage metadata updates when explicitly justified
- Any non-present canonical mutation requires explicit override + reason.

### 7) Custody-Chain Visibility Normalization
- Preflight computes scene visibility from custody chain, not just local posture text.
- Example normalization rule:
  - item says `container=pack_a`
  - pack has `location_ref=inn_room_3`
  - character is in `market_square`
  - result: item exists in custody but is not visible/carried in scene
- This rule directly supports "stowed at inn" transitions.

### 8) Canonical Naming Policy (UI vs Prose)
- Authoritative UI/system surfaces must use canonical names/IDs.
- Narrative prose may use aliases/synonyms.
- Lint should fail only when authoritative UI labels drift from canon, not for prose synonymy.

### 9) Slice-Aware Missing Canon Handling
- Scene prompts use compact canonical slices, not full registry by default.
- If phase references unknown-in-slice ID, do not treat as unknown-in-canon immediately.
- Failure mode should request targeted slice expansion for the missing ID/thread and retry.
- Prevents retry thrash due to context omission.

### 10) Idempotent Commit Beyond Attempt IDs
- Add commit ledger with two guards:
  - scene commit finalization guard (`book/chapter/scene/phase`)
  - mutation hash guard over canonical mutation blocks
- Reapplying logically identical patch under a different attempt id must no-op.
- Prevents double decrement/double transfer during retries/replays.

## Canonical Data Model

### Character Inventory (Scene View)
- Keep character posture as local scene-facing view:
  - `inventory_instances`
  - `inventory_posture`
  - `inventory_notes`
- Minimum item fields:
  - `item_id`
  - `item_name`
  - `quantity`
  - `owner_scope`
  - `status` (`equipped|carried|stowed|cached|lost|consumed|broken`)
  - `container`
  - `scene_last_updated`
  - optional custody-chain pointers (`container_ref`, `carrier_ref`, `location_ref`)

### Item Registry (Durable Canon)
- File: `draft/context/item_registry.json`
- Required fields:
  - `item_id`, `name`, `type`
  - `owner_scope`
  - `custodian`
  - `linked_threads`
  - `state_tags`
  - `last_seen`
  - optional `linked_device_id`

### Plot Device Registry (Durable Canon)
- File: `draft/context/plot_devices.json`
- Handles physical and intangible devices.
- Required fields:
  - `device_id`, `name`
  - `custody_scope`, `custody_ref`
  - `activation_state`
  - `linked_threads`
  - `constraints`
  - `last_seen`
  - optional `linked_item_id`

## State Patch Contract Extensions
- Add or enforce blocks:
  - `inventory_alignment_updates`
  - `item_registry_updates`
  - `plot_device_updates`
  - `transfer_updates`
- Operation model:
  - `set`, `delta`, `remove`, `reason`
- Require `reason` for:
  - off-screen transition normalizations
  - non-present allowed canonical updates

## Full Writing Loop Integration (Structural + Prompt)

### Planning
- Extend scene card schema with:
  - `required_in_custody`
  - `required_visible`
  - `forbidden_visible`
  - `device_presence`
  - `transition_type` (`continuous|time_skip|location_jump|aftermath|flashback`)
  - `timeline_scope`
- Prompt hardening:
  - explicit distinction between existence and visibility constraints.

### Preflight
- Inputs:
  - cast character states
  - item registry slice
  - plot-device slice
  - previous scene prose / cast last appearance prose
  - minified full outline (system context)
- Responsibilities:
  - posture normalization
  - custody-chain visibility resolution
  - transfer prep if scene intent requires
  - emit reasons for implicit transitions
- Output:
  - patch-only canonical updates

### Continuity Pack
- Build from post-preflight canonical state.
- Include compact state slices:
  - visible equipment now
  - stowed-but-critical items
  - active devices relevant to scene threads
- Optional minified outline injection when ordering drift occurs.

### Write
- Inputs include aligned canonical slices + minified full outline.
- Writer must mirror any inventory/device mutation in patch blocks.
- Prose-only mutations are invalid and should fail downstream.

### State Repair
- Inputs include prose + patch + canonical slices + minified full outline.
- Completes missing canonical updates conservatively.
- Must respect timeline scope gating.

### Lint
- Deterministic tripwires only (smoke detectors, not extractors):
  - custody/posture contradiction
  - transfer incompleteness
  - timeline policy violation
  - canonical UI naming drift
  - required/forbidden visibility violations

### Repair
- Reconciles contradictions and outputs corrected patch.
- Must preserve scene intent while restoring canonical consistency.

### Apply/Commit
- Enforce:
  - schema validity
  - authority precedence
  - transfer atomicity
  - idempotent commit guards
  - timeline mutation policy
- Commit as one scene transaction.

## Minified Outline Injection Policy
- Required by default:
  - `preflight`, `write`, `state_repair`, `repair`
- Optional/toggled:
  - `continuity_pack` (on when ordering drift patterns observed)
  - `lint` (off by default)
- Add per-phase env toggles for outline injection control to manage token cost.

## Prompt Hardening Scope
- Update templates:
  - `plan.md`
  - `preflight.md`
  - `continuity_pack.md`
  - `write.md`
  - `state_repair.md`
  - `lint.md`
  - `repair.md`
- Enforce language:
  - state mutation must be in patch
  - non-present canonical mutation policy
  - transfer must be atomic
  - canonical IDs on authoritative surfaces

## Parser And Apply Hardening
- Strictly validate new blocks and transfer shapes.
- Keep non-LLM fixups limited to shape coercion/type normalization.
- No canonical inference from prose.
- Return actionable path-level errors.

## Migration And Deterministic IDs
- First-run migration:
  - backfill item registry from character inventories
  - backfill plot devices from known continuity/device hints
  - mark uncertain entries `unclassified`
- Deterministic ID policy:
  - same source data maps to same IDs across reruns/resets
- Migration idempotent by design.

## History And Debugability
- Keep character snapshots before preflight mutation.
- Add registry snapshots before mutation:
  - `draft/context/items/history/chXXX_scYYY_item_registry.json`
  - `draft/context/plot_devices/history/chXXX_scYYY_plot_devices.json`
- Add per-scene commit ledger entries with:
  - `scene_patch_id`
  - mutation hash
  - phase
  - commit outcome

## Reset Command Hardening
- Extend `bookforge reset-book` to clear runtime-only context:
  - continuity pack/history
  - chapter summaries
  - generated scene/chapter output
  - item/plot registries + indexes + histories
  - character histories
  - runtime preflight/state-repair artifacts
- Preserve author/library canonical assets.
- Regenerate missing runtime state at next run start.
- Log cleanup flags:
  - `--keep-logs` default false
  - `--logs-scope book|all` default `book`
- Console output must include:
  - stage start/end
  - per-domain deletion counts
  - final summary totals

## Expanded Edge Cases
- "Stowed at inn" chain correctness across travel/time-skip scenes.
- Character absent for many scenes returns with stale carried state.
- Handoff implied in prose without transfer block.
- Quantity split transfers across two characters.
- Item consumed/broken and later referenced.
- Duplicate display names with different IDs.
- Flashback/dream/sim scene tries to mutate present canonical custody.
- Non-present scene legitimately updates knowledge-type intangible device.
- Retry after partial failure attempts to reapply same mutation.
- Missing slice data causes unknown-ID false failure.
- Device linked to multiple threads where one resolves earlier.
- Truncated/missing previous scene prose in preflight context.

## Stories (Implementation Order)

### Story A: Schema + Canonical Files
- Implement schemas and bootstrap files for item/device domains and patch blocks.
- DoD:
  - schema validators pass
  - bootstrap files generated deterministically

### Story B: Authority + Timeline + Idempotent Commit
- Implement precedence, timeline scope gating, and two-level commit dedupe.
- DoD:
  - duplicate apply no-op verified
  - non-present physical custody mutations blocked unless override

### Story C: Transfers + Custody-Chain Visibility
- Implement `transfer_updates` atomic apply and visibility normalization chain.
- DoD:
  - handoff and stowed-at-inn fixtures pass without drift

### Story D: Loop-Wide Prompt + Context Upgrade
- Update all phase prompts and payload builders.
- Inject minified outline by policy.
- DoD:
  - no missing fields
  - phase prompts contain explicit mutation constraints

### Story E: Lint/Repair Blocking Pipeline
- Add deterministic checks and slice-aware retry expansion logic.
- DoD:
  - contradiction fixtures block, repair, and either pass or pause with explicit reason

### Story F: Migration + History + Reset
- Implement deterministic migration, snapshots, and reset hardening/logging.
- DoD:
  - reset returns post-outline baseline
  - histories and logs are clear and reproducible

### Story G: End-To-End Regression
- Add long-run chapter fixtures for LitRPG/fantasy/intangible-device scenarios.
- DoD:
  - chapter runs complete with no unresolved blocking inventory/device continuity failures.