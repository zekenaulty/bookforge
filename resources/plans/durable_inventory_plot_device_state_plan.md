# Durable Inventory And Plot Device State Plan (Refined v4)

## Purpose
- Prevent long-run inventory and plot-device continuity drift while keeping BookForge a thin orchestration engine.
- Preserve prose freedom, enforce canonical truth only on authoritative state surfaces.
- Support off-screen transitions (for example: "stowed at inn") with deterministic, auditable state alignment.

## In-Scope
- Inventory posture/custody continuity.
- Physical and intangible plot-device continuity.
- Idempotent, retry-safe state commits.
- Full writing loop integration: planning, preflight, continuity, write, state repair, lint, repair, apply/commit, reset.

## Out-Of-Scope
- Full game simulation.
- Broad prose-to-state extraction as primary truth.
- Genre-specific hardcoding beyond shared continuity mechanics.

## Fixed Architecture Decisions
- Prefer explicit domain files over overloaded state monoliths.
- Canonical files:
  - `draft/context/item_registry.json`
  - `draft/context/plot_devices.json`
  - `draft/context/items/index.json` (optional)
  - `draft/context/plot_devices/index.json` (optional)
  - `draft/context/items/history/*.json`
  - `draft/context/plot_devices/history/*.json`
- Keep thread linkage in canonical entries (`linked_threads`).
- Lint severity semantics:
  - `warn`: advisory
  - `fail`: blocking and enters retry flow
- Inventory/device high-confidence contradictions default to `fail`.

## Operational Semantics (Authoritative)

### 1) Authority Boundary And Precedence
- Canonical custody truth:
  - `item_registry` for items
  - `plot_devices` for devices
- Character inventory is scene-local posture/view.
- Conflict resolution:
  - if registry custody and character posture disagree, custody wins
  - preflight/state_repair/repair normalize posture toward custody unless scene intent/patch explicitly changes custody
- Prose never mutates canon directly.

### 2) Authoritative Surface Detection (Critical For Prose Freedom)
- Canonical naming/ID enforcement applies only to authoritative blocks:
  - system UI panels
  - inventory/stat blocks
  - system notifications
  - structured patch payloads
- Non-authoritative narrative prose can use aliases/synonyms.
- Lint must classify block type before applying canonical-name checks.
- Unknown block type defaults to non-authoritative unless explicitly tagged authoritative.

### 3) Mutation Channels (No Silent Mutations)
- Valid mutation channels:
  - planning intent fields
  - patch blocks from `preflight`, `write`, `state_repair`, `repair`
- Invalid channel:
  - prose implication without patch representation
- Blocking condition:
  - prose claims transfer/consumption/breakage and patch omits canonical updates.

### 4) Mutation Preconditions (Stale Overwrite Guard)
- Canonical mutation blocks may include optional preconditions:
  - `expected_before` snapshots or hashes
  - expected custody/status/quantity before apply
- If precondition mismatch occurs:
  - fail with conflict code and route to repair/retry
- Prevents stale state overwrites during reruns and delayed retries.

### 5) Deletion And Tombstone Policy
- Durable records are tombstoned by default, not hard-deleted.
- `remove` for durable entries maps to tombstone transition unless explicitly ephemeral.
- Tombstone minimum:
  - `state_tags` includes `destroyed|consumed|lost|retired`
  - `last_seen`
  - optional `resolution_note`
- Hard delete reserved for ephemeral runtime artifacts and deterministic migration cleanup only.

### 6) Transfer Semantics: Atomic, Closed-World, Multi-Hop
- Standard transfer uses `transfer_updates` with atomic requirements:
  - source posture/state
  - destination posture/state
  - registry custody
- Multi-hop transfer support:
  - one transaction can include carrier/container/location chain updates
  - example: `character -> pouch -> chest -> inn`
- Partial apply is invalid and must abort commit.

### 7) Stack And Identity Rules
- Unique items: single `item_id`, no concurrent duplicate custody.
- Fungible stacks:
  - either quantity deltas under shared `item_id`
  - or split `inventory_instance_id` entries
- Split transfer patches must specify source and destination quantity effects explicitly.

### 8) Timeline And Ontology Scope Gating
- Add scene-level scope fields:
  - `timeline_scope`: `present|flashback|dream|simulation|hypothetical`
  - `ontological_scope`: `real|non_real`
- Canonical mutation policy:
  - physical custody changes allowed only when `timeline_scope=present` and `ontological_scope=real`, unless explicit override
- Controlled non-present/non-real allowed updates:
  - knowledge-like intangible updates
  - linkage metadata updates with reason category

### 9) Visibility Semantics Split
- Distinguish constraints:
  - `required_in_custody` (exists in canonical custody)
  - `required_scene_accessible` (retrievable/usable without continuity break)
  - `required_visible_on_page` (optional narrative requirement)
  - `forbidden_visible`
- Default strict enforcement focuses on custody/accessibility, not forced prose mention.

### 10) Custody-Chain Visibility Normalization
- Preflight computes visibility/accessibility from chain pointers:
  - `container_ref`, `carrier_ref`, `location_ref`
- Example:
  - item in `pack_a`, pack at `inn_room_3`, character in `market_square`
  - result: item in custody, not scene-accessible unless retrieval transition is declared.

### 11) Canonical Naming And Alias Layer
- Canonical names/IDs mandatory on authoritative surfaces.
- Add optional alias map in registry for matching/expansion support.
- Block only taxonomy drift in authoritative surfaces, not prose synonym variation.

### 12) Slice-Aware Retry Expansion With Bounds
- Unknown-in-slice is not immediately unknown-in-canon.
- On missing slice reference, use deterministic slice request contract:
  - by `item_id`
  - by `device_id`
  - by `thread_id`
  - by linked container/custody chain
- Expansion retries are bounded per phase (max N expansions) to avoid thrash loops.

### 13) Idempotent Commit Model (Beyond Attempt IDs)
- Two-level dedupe guards:
  - scene-phase finalization guard
  - mutation hash guard over canonical mutation blocks
- Replaying same logical mutation under different attempt IDs must no-op.

### 14) Linked Item-Device Consistency Rules
- For linked entries (`linked_item_id`/`linked_device_id`):
  - custody refs cannot contradict each other without explicit transition
  - activation states cannot imply presence of tombstoned counterpart
- Lint emits paired-consistency failures where violated.

### 15) Tombstone Revival Rules
- Revival must be explicit:
  - `revive` transition with reason and lineage
- If replacing rather than reviving:
  - create new instance with `replacement_of=<old_id>` linkage
- Silent resurrection is invalid.

## Canonical Data Model

### Character Inventory (Scene View)
- Fields:
  - `inventory_instances`
  - `inventory_posture`
  - `inventory_notes`
- Minimum per instance:
  - `item_id`, `item_name`, `quantity`, `owner_scope`, `status`, `container`, `scene_last_updated`
  - optional: `container_ref`, `carrier_ref`, `location_ref`

### Item Registry (Durable Canon)
- File: `draft/context/item_registry.json`
- Required fields:
  - `item_id`, `name`, `type`, `owner_scope`, `custodian`, `linked_threads`, `state_tags`, `last_seen`
- Optional:
  - `aliases`
  - `linked_device_id`
  - `replacement_of`

### Plot Device Registry (Durable Canon)
- File: `draft/context/plot_devices.json`
- Supports physical and intangible devices.
- Required:
  - `device_id`, `name`, `custody_scope`, `custody_ref`, `activation_state`, `linked_threads`, `constraints`, `last_seen`
- Optional:
  - `aliases`
  - `linked_item_id`

## State Patch Contract Extensions
- Add/enforce blocks:
  - `inventory_alignment_updates`
  - `item_registry_updates`
  - `plot_device_updates`
  - `transfer_updates`
- Block operation model:
  - `set`, `delta`, `remove`, `reason`, optional `reason_category`, optional `expected_before`
- Required fields by case:
  - off-screen normalization must include `reason` + `reason_category`
  - non-present/non-real allowed updates must include explicit override intent

## Reason Category Taxonomy
- Machine-readable categories for off-screen and exceptional transitions:
  - `time_skip_normalize`
  - `location_jump_normalize`
  - `after_combat_cleanup`
  - `stowed_at_inn`
  - `handoff_transfer`
  - `knowledge_reveal`
  - `timeline_override`
- Keep freeform note text optional in addition to category.

## Full Writing Loop Integration (Structural + Prompt)

### Planning
- Scene card fields:
  - `required_in_custody`
  - `required_scene_accessible`
  - `required_visible_on_page` (optional)
  - `forbidden_visible`
  - `device_presence`
  - `transition_type`
  - `timeline_scope`
  - `ontological_scope`
- Prompt updates:
  - explicit custody/accessibility/visibility distinction
  - intent requirements for custody/device changes

### Preflight
- Inputs:
  - cast character states
  - item/device canonical slices
  - previous scene + last-appearance context
  - minified full outline in system context
- Responsibilities:
  - posture/custody-chain normalization
  - apply intended transitions
  - generate explicit reason categories
  - reject ambiguous transitions as `fail`
- Output:
  - patch-only canonical updates

### Continuity Pack
- Build from post-preflight canonical state.
- Include compact slices:
  - visible now
  - scene-accessible but off-page critical items
  - active thread-relevant devices
- Optional outline injection when ordering drift appears.

### Write
- Receives canonical slices + minified outline.
- Any mutation must be mirrored in patch blocks.
- Prompt forbids prose-only canonical mutation.

### State Repair
- Receives prose + patch + canonical slices + minified outline.
- Conservative completion only when high-confidence and scene intent compatible.
- Ambiguous mutation => fail with explicit guidance, not guessed repair.

### Lint
- Deterministic checks only:
  - authoritative-surface canonical checks
  - custody/posture contradictions
  - transfer completeness
  - scope-policy violations
  - linked pair consistency
  - visibility/accessibility constraint violations

### Repair
- Reconciles contradictions and outputs corrected patch.
- Preserves story intent while restoring canonical consistency.

### Apply/Commit
- Enforces:
  - schema validity
  - precedence rules
  - preconditions
  - transfer atomicity
  - scope policy
  - idempotent dedupe guards
- Commit remains scene-transactional.

## Minified Outline Injection Policy
- Required by default:
  - `preflight`, `write`, `state_repair`, `repair`
- Optional/toggled:
  - `continuity_pack`
  - `lint`
- Add per-phase env toggles for outline injection to manage token budget.

## Prompt Hardening Scope
- Update templates:
  - `plan.md`
  - `preflight.md`
  - `continuity_pack.md`
  - `write.md`
  - `state_repair.md`
  - `lint.md`
  - `repair.md`
- Enforce language for:
  - authoritative mutation surfaces
  - transfer requirements
  - scope gating
  - reason categories
  - ambiguity handling

## Parser And Apply Hardening
- Strict schema and path-level errors for all new blocks.
- Non-LLM fixups limited to structural coercion and type normalization.
- No canonical mutation inference from prose.

## Migration And Deterministic IDs
- First run migration:
  - backfill item registry from character inventories
  - backfill plot devices from known continuity hints
  - mark uncertain entries `unclassified`
- Deterministic ID generation required.
- Idempotent migration required.

## History And Debugability
- Keep character snapshots pre-preflight.
- Add item/device snapshot artifacts pre-mutation:
  - `draft/context/items/history/chXXX_scYYY_item_registry.json`
  - `draft/context/plot_devices/history/chXXX_scYYY_plot_devices.json`
- Add commit ledger entries:
  - `scene_patch_id`, mutation hash, phase, apply status, conflict reason if any.

## Reset Command Hardening
- `bookforge reset-book` clears runtime-only artifacts:
  - continuity pack/history
  - chapter summaries
  - generated scene/chapter output
  - item/device registries + indexes + histories
  - character histories
  - preflight/state-repair runtime artifacts
- Preserve author/library assets.
- Regenerate runtime state at run start deterministically.
- Flags:
  - `--keep-logs` default false
  - `--logs-scope book|all` default `book`
- Console output:
  - stage start/end
  - per-domain deletion counts
  - final summary totals

## Expanded Edge Cases
- Stowed-at-inn chain across travel jump.
- Human prose edit implies mutation but no patch exists.
- Out-of-order scene generation and chronology conflict.
- Handoff implied in prose without transfer block.
- Partial stack split transfer with nested containers.
- Item consumed/broken then referenced later.
- Duplicate display names with distinct IDs.
- Non-present/non-real scenes mutating present canon improperly.
- Legitimate knowledge reveal in non-present scope.
- Retry replay with logically identical mutation under different attempt IDs.
- Missing slice data causing repeated unknown-ID failures.
- Linked item/device diverge after one-sided mutation.
- Thread retires device while another thread still depends on it.
- Truncated previous scene prose in preflight context.

## Progress Tracking (Live)
- As-of: 2026-02-07
- Tracking mode:
  - `done`: DoD met end-to-end.
  - `in_progress`: partially implemented; remaining scope listed.
  - `pending`: not implemented yet.

### Current Story Status
- [x] Story A (`done`): Schema And Canonical Contracts
- [x] Story B (`done`): Apply Engine Semantics
- [x] Story C (`done`): Transfer + Visibility Chain
- [x] Story D (`done`): Loop-Wide Prompt And Context Upgrade
- [x] Story E (`done`): Lint/Repair Retry Discipline
- [x] Story F (`done`): Migration, Snapshots, Reset
- [x] Story G (`done`): Long-Run Regression Suite

### Implemented So Far (Turn Log)
- Turn 1 (completed):
  - Added durable canonical schemas and schema registration.
  - Extended `state_patch` for durable blocks.
  - Added durable state module and exports.
  - Wired workspace init/reset for durable runtime artifacts.
  - Wired runner phase contexts for `item_registry` and `plot_devices`.
  - Added authoritative-surface extraction and surface-aware stat mismatch checks.
  - Updated prompt templates for durable canonical context.
  - Validation: `60 passed`.
- Turn 2 (completed):
  - Added persistent durable commit ledger and index maintenance.
  - Implemented transactional durable mutation apply path.
  - Added atomic transfer handling and mutation hash dedupe across reruns.
  - Wired durable apply into preflight and final scene apply.
  - Reset now clears durable commit ledger.
  - Prompt hardening for explicit durable mutation blocks.
  - Validation: `64 passed`.
- Turn 3 (completed):
  - Added scene-scope gating (`timeline_scope`, `ontological_scope`) for durable mutations in apply path.
  - Enforced non-present/non-real scope policy with explicit override support for physical mutations.
  - Added per-phase minified-outline system prompt toggles via env (`BOOKFORGE_<PHASE>_INCLUDE_OUTLINE`).
  - Extended scene-card schema and planner normalization with continuity scope/visibility fields.
  - Added deterministic item-registry backfill migration from character runtime state when registry is empty.
  - Added regression tests for scope gating, scene-card defaults, and migration determinism.
  - Validation: `67 passed`.
- Turn 4 (completed):
  - Completed transfer-chain semantics so transfer endpoints can be derived from `transfer_chain` (first hop source, last hop destination).
  - Persisted `last_transfer_chain` on durable item entries for forensic debugging and replay analysis.
  - Added deterministic durable lint checks driven by scene-card constraints:
    - `required_in_custody`
    - `required_scene_accessible`
    - `required_visible_on_page`
    - `forbidden_visible`
    - `device_presence`
  - Added linked item/device consistency checks for tombstone-vs-activation and custody conflicts.
  - Added structured `durable_slice_missing` retry hints for missing context IDs.
  - Added regression tests for durable constraint checks and link consistency checks.
  - Validation: `73 passed`.

- Turn 5 (completed):
  - Hardened phase prompts (`preflight`, `write`, `lint`, `state_repair`, `repair`) to explicitly enforce scene-card durable constraints and scope gates.
  - Added deterministic lint checks for scene-card durable constraints and linked item/device consistency in runner.
  - Added regression tests for durable constraint failures, slice-missing detection, and link-state conflicts.
  - Updated run help docs with per-phase outline injection env toggles and usage example.
  - Validation: `73 passed`.
- Turn 6 (completed):
  - Added strict-mode reason-coded pause behavior for unresolved `durable_slice_missing` lint failures after repair.
  - Added generic pause helpers for non-quota deterministic stop conditions:
    - `_write_reason_pause_marker`
    - `_pause_on_reason`
  - Added lint issue helpers for targeted issue-code extraction:
    - `_lint_issue_entries`
    - `_lint_has_issue_code`
  - Added regression test ensuring reason-coded pause marker creation.
  - Validation: `74 passed`.

- Turn 7 (completed):
  - Implemented bounded durable-slice expansion retries in run loop:
    - Scene-level expansion tracking (`durable_expand_ids`, attempts, max).
    - Targeted expansion IDs extracted from lint `retry_hint` entries.
    - Re-run repair/state_repair/lint with expanded durable slice until pass or bounds reached.
  - Added durable slice sizing support in context builder:
    - `_durable_state_context(..., expanded_ids=...)` now returns scene-relevant slices by default and includes targeted expansions.
  - Added helper APIs for expansion flow:
    - `_durable_slice_max_expansions`
    - `_durable_slice_retry_ids`
  - Extended strict failure pause details with expansion telemetry (`attempts`, `max`, `expanded_ids`).
  - Added regression tests for durable slicing and retry-hint extraction.
  - Validation: `76 passed`.
- Turn 8 (completed):
  - Completed deterministic plot-device migration backfill from continuity hints (state/outline/continuity thread references) when `plot_devices.json` is empty.
  - Added stable seeded device IDs and thread-linked canonical defaults (`custody_scope=thread`, `activation_state=tracked`).
  - Hardened `book reset` with detailed runtime cleanup reporting and log-scope controls (`book|all`, optional `--keep-logs`).
  - Expanded reset cleanup to include pause markers and full durable runtime reinitialization.
  - Added regression tests for plot-device migration determinism and reset log-clearing behavior.
  - Validation: `79 passed`.

- Turn 9 (completed):
  - Added durable commit chronology guard to block out-of-order scene applies (prevents stale rollback drift).
  - Extended durable commit ledger format with `latest_scene` tracking (`chapter`, `scene`).
  - Added regression test for chronology conflict handling in long-run rerun scenarios.
  - Updated durable commit normalization tests for new ledger shape.
  - Validation: `81 passed`.

- Turn 10 (completed):
  - Enabled non-present/non-real intangible plot-device custody transitions with explicit `reason_category` policy enforcement.
  - Added durable-apply pause wrapper so chronology conflicts create deterministic `run_paused.json` markers (`durable_chronology_conflict`) instead of silent hard-fail exits.
  - Added regression tests for:
    - intangible custody transition allow/block behavior in flashback/non-real scenes,
    - strict pause marker generation for chronology conflicts,
    - linked item/device drift detection after real mutation across scene progression.
  - Validation: `85 passed`.

- Turn 11 (completed):
  - Root-caused first schema hard-fail from live run: `character_updates[].inventory` emitted as string item ids in repair output.
  - Hardened prompts (`write`, `repair`, `state_repair`, `preflight`) to require inventory object arrays explicitly and added strict object-shape examples.
  - Added defensive coercion in `runner` so string inventory entries are normalized to object entries using in-patch inventory alignment and container hints before schema validation.
  - Added regression tests for inventory-string coercion and object normalization in `tests/test_state_bag_and_milestones.py`.
  - Validation: `87 passed`.

- Turn 12 (completed):
  - Added schema-validation retry loops for all state-patch emitting phases (`preflight`, `write`, `repair`, `state_repair`) so schema misses trigger corrective LLM retries before hard fail.
  - Added centralized state-patch normalization helper and transfer-update coercion (`_coerce_transfer_updates`) to enforce object-shape arrays and required `reason` fallback semantics before schema validation.
  - Hardened system/output and phase prompt contracts with explicit rule: every `transfer_updates` object must include `item_id` and non-empty `reason`.
  - Synced updated templates into active book workspace (`book update-templates --book criticulous_b1`).
  - Added regression tests for transfer-update coercion and required reason fallback in `tests/test_state_bag_and_milestones.py`.
  - Validation: `91 passed`.

- Turn 13 (completed):
  - Added inventory_alignment_updates coercion to accept legacy wrapper objects with `updates` and fan-out into list entries with inherited reason/category.
  - Added schema-validation retry loops for inventory alignment shape errors via centralized state patch normalization.
  - Hardened prompts/system/output contract to require inventory_alignment_updates be an array (no wrapper object).
  - Added regression test for inventory alignment unwrap coercion.
  - Synced updated templates into active book workspace (`book update-templates --book criticulous_b1`).
  - Validation: `92 passed`.

- Turn 14 (completed):
  - Added display/prose naming support for durable items (`display_name`) and normalized item names derived from ITEM_* IDs.
  - Normalized item registry entries on load/save/ensure to populate display_name/name when missing or when name equals item_id.
  - Updated transfer handling and on-page mention matching to prefer display_name/name for prose detection.
  - Hardened prompts/system/output contract to instruct prose to use display_name/name and reserve item_id for JSON/patches.
  - Added regression test ensuring ITEM_* names are humanized into display_name.
  - Synced updated templates into active book workspace (`book update-templates --book criticulous_b1`).
  - Validation: `93 passed`.


### Remaining Scope By Story
- Story B remaining:
  - None (DoD met in current implementation pass).
- Story C remaining:
  - None (DoD met in current implementation pass).
- Story D remaining:
  - None (DoD met in current implementation pass).
- Story E remaining:
  - None (DoD met in current implementation pass).
- Story F remaining:
  - None (DoD met in current implementation pass).
- Story G remaining:
  - None (DoD met in current implementation pass).
  
## Stories (Implementation Order)

### Story A: Schema And Canonical Contracts
- Implement schemas for new blocks and canonical files.
- Add authoritative-surface tagging rules and reason category enums.
- DoD:
  - schema validators pass
  - authoritative-surface detection fixtures pass

### Story B: Apply Engine Semantics
- Implement precedence, preconditions, scope gating, transfer atomicity, and idempotent dedupe.
- DoD:
  - no duplicate apply on retries
  - stale overwrite precondition conflicts surfaced cleanly

### Story C: Transfer + Visibility Chain
- Implement transfer graph updates and custody-chain visibility normalization.
- DoD:
  - stowed-at-inn and multi-hop transfer fixtures pass

### Story D: Loop-Wide Prompt And Context Upgrade
- Update all phase prompts/context payloads.
- Inject minified outline by policy.
- DoD:
  - no missing prompt fields
  - mutation guidance consistent across phases

### Story E: Lint/Repair Retry Discipline
- Add deterministic checks, slice-aware expansion contract, bounded expansion retries, conservative repair confidence rules.
- DoD:
  - contradiction fixtures resolve or pause with explicit reason codes

### Story F: Migration, Snapshots, Reset
- Implement deterministic migration, history snapshots, and reset hardening/logging.
- DoD:
  - reset returns post-outline baseline
  - deterministic IDs preserved across reruns

### Story G: Long-Run Regression Suite
- Add multi-chapter fixtures including human-edit, out-of-order generation, thread-device overlap, intangible custody transitions.
- DoD:
  - no unresolved blocking continuity failures in long-run scenarios.


