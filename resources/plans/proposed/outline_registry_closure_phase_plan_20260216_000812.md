# Outline Registry Closure Phase Plan (20260216_000812)

## Purpose
Add a dedicated phase after outline generation and before drafting whose only job is to close identity registries so the outline contains no ghost references.

This phase guarantees:
1. Every character referenced by the outline exists in the character registry.
2. Every location referenced by the outline exists in the location registry.
3. Drafting cannot start while unresolved outline references remain.

## Scope (This Plan)
In scope:
1. New post-outline phase for registry closure.
2. Character registry completeness from outline references.
3. Location registry completeness from outline references/hooks.
4. Deterministic validation and draft gating.
5. Artifact/report outputs for auditability.
6. Model/key routing split between character and location closure tasks.

Out of scope:
1. Rich character embodiment from prose.
2. Prose-time entity extraction redesign.
3. New scene creation logic in outline phases.
4. Character/location enrichment beyond minimal identity completeness.

## Non-Negotiable Constraints
1. This phase is completeness-first, not creativity-first.
2. It must not invent deep characterization or lore.
3. It may create minimal records when an entity is referenced but missing.
4. Registry IDs must be stable and deterministic once assigned.
5. Drafting is blocked if unresolved references remain after retries.

## Pipeline Placement
Insert new phase:
1. Outline pipeline complete.
2. Registry closure phase (new).
3. Drafting/writing loop begins.

Proposed phase id:
1. `outline_registry_closure`

## Phase Contract
### Inputs
1. Final outline artifact (`outline/outline.json` and chapter files as needed).
2. Active outline location registry (if present).
3. Character registry/index files.
4. Existing location registry/index files (runtime or outline-published source).
5. Book metadata and targets for context.

### Outputs
1. Updated character registry/index with minimal complete entries.
2. Updated location registry/index with minimal complete entries.
3. Closure report with counts and reason-coded actions.
4. Validation report proving no unresolved outline references remain.

### Hard Gate
Drafting may proceed only when:
1. `unresolved_character_refs == 0`
2. `unresolved_location_refs == 0`
3. Closure report status is `SUCCESS` or `SUCCESS_WITH_WARNINGS` (warnings must be non-blocking by policy).

## Entity Harvest Rules
### Character Harvest (Outline-Time)
Harvest from outline fields that can carry character identity:
1. scene cast/presence lists.
2. introduces lists.
3. explicit character mentions in structured fields.
4. top-level outline character arrays.

For each harvested character reference:
1. Match existing canonical character by stable ID first.
2. If ID absent but name/alias matches existing canonical record, reuse and attach alias evidence.
3. If no match, create minimal character record.

Minimal character record requirement:
1. `character_id`
2. `display_name` (or placeholder label if missing with unresolved flag)
3. `origin: outline_registry_closure`
4. `introduced_at` (chapter/scene)
5. `status: candidate` (or equivalent minimal lifecycle status)

### Location Harvest (Outline-Time)
Harvest from outline fields carrying location identity/hints:
1. scene `location_start_id` / `location_end_id`
2. location labels/hooks
3. chapter/section location bridge fields where applicable
4. top-level outline location registries

For each harvested location reference:
1. Match existing canonical location by ID first.
2. If ID absent, attempt deterministic label-to-id resolution.
3. If no match, create minimal location record.

Minimal location record requirement:
1. `location_id`
2. `display_name`
3. `origin: outline_registry_closure`
4. `introduced_at` (chapter/scene)
5. optional `parent_location_id` if resolvable

## Identity and Dedup Policy
1. Prefer canonical ID match over label match.
2. Label/alias matching may suggest candidates but cannot silently merge high-confidence conflicts.
3. Ambiguous matches must emit `requires_human_decision` or trigger targeted retry.
4. Never overwrite an existing canonical entity with weaker inferred data.

## Model and API Routing Policy
Character closure subtask:
1. Use character API key.
2. Use character model.

Location closure subtask:
1. Use default API key.
2. Use default model.

Deterministic orchestrator responsibility:
1. Split tasks by domain.
2. Route each subtask to its configured key/model.
3. Record key/model route in phase report metadata.

## Retry and Failure Policy
1. Max attempts per subtask: 2 by default (configurable).
2. Retry only with bounded fix list (missing fields, unresolved refs, collisions).
3. On exhaustion, return terminal `ERROR` with reason codes.
4. No silent fallback to drafting.

Reason code examples:
1. `character_ref_unresolved`
2. `location_ref_unresolved`
3. `entity_id_collision`
4. `entity_merge_ambiguous`
5. `registry_write_failed`

## Artifacts and Reporting
Proposed artifacts under outline run path:
1. `registry_closure_input_snapshot.json`
2. `registry_closure_character_output.json`
3. `registry_closure_location_output.json`
4. `registry_closure_validation.json`
5. `registry_closure_report.json`

Report minimum fields:
1. `overall_status`
2. `created_character_count`
3. `updated_character_count`
4. `created_location_count`
5. `updated_location_count`
6. `unresolved_character_refs`
7. `unresolved_location_refs`
8. `attention_items[]`
9. `model_routes` (character/location route metadata)

## Integration Touchpoints (Expected)
Code:
1. `src/bookforge/outline.py` (phase orchestration + gating hook)
2. `src/bookforge/runner.py` (write-start gate integration)
3. `src/bookforge/characters.py` (registry/index upsert helpers)
4. new location registry helper module (if not already shared)
5. run logging / phase history modules

Prompts:
1. new character registry closure prompt template
2. new location registry closure prompt template
3. optional shared prompt block for closure contract

Schemas:
1. closure output schema(s)
2. closure report schema
3. potential minimal entity schema adjustments if needed

Docs:
1. `docs/help/outline_generate.md`
2. `docs/help/run.md`
3. phase reference docs for new closure phase

## Deterministic Validation Rules
1. Every outline character ref resolves to a registry entry.
2. Every outline location ref resolves to a registry entry.
3. No duplicate IDs in either registry.
4. No duplicate canonical records from same source ref.
5. Registry writes are idempotent across reruns.

## Resume and Rerun Behavior
1. Phase rerun allowed independently if outline fingerprint unchanged.
2. If outline fingerprint changed, closure phase must rerun before drafting.
3. Closure artifacts include provenance hash of outline inputs.
4. Resume must refuse stale closure artifacts when provenance mismatches.

## Acceptance Tests (Draft)
1. Missing character refs in outline are converted into minimal registry records.
2. Missing location refs in outline are converted into minimal registry records.
3. Ambiguous duplicate candidate causes `requires_human_decision` or retry, not silent merge.
4. Drafting is blocked when unresolved refs remain.
5. Rerun with unchanged outline is idempotent (no duplicate entity creation).
6. Rerun after outline mutation invalidates prior closure output.
7. Character subtask and location subtask use correct key/model routes (logged and testable).

## Risks and Mitigations
1. Risk: false merges from fuzzy name matching.
   - Mitigation: conservative merge thresholds + ambiguity escalation.
2. Risk: ID churn across reruns.
   - Mitigation: deterministic ID generation and alias policy.
3. Risk: closure phase increases run time.
   - Mitigation: bounded retries and domain-split processing.
4. Risk: blocked drafting during early tuning.
   - Mitigation: explicit reports and operator-visible fix reasons.

## Open Design Questions (For Next Discussion)
1. Should location closure use outline location registry as source-of-truth and publish runtime copy, or maintain separate runtime-first registry?
2. Should minimal character records be `candidate` or `promoted_minimal` by default?
3. What ambiguity threshold triggers hard stop vs warning + human ack?
4. Should closure run as one phase with two subtasks, or two explicit phases (`character_registry_closure`, `location_registry_closure`)?
5. Should closure be mandatory for all books or flag-gated during rollout?

## Proposed Execution Order
1. Define closure schemas and report contract.
2. Implement deterministic harvest + validation layer.
3. Implement character closure prompt and routing.
4. Implement location closure prompt and routing.
5. Wire phase orchestration and draft gate.
6. Add tests and docs.
7. Pilot on `criticulous_b1` and audit reports before broad rollout.
