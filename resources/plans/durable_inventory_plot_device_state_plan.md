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