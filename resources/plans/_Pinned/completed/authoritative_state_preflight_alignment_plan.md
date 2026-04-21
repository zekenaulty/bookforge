# Authoritative State + Preflight Alignment Plan

## Purpose
- Correct continuity and mechanic drift by making LLM-authored `state_patch` the sole source of state changes.
- Replace brittle UI/prose-to-state fallbacks with explicit state authoring in dedicated phases.
- Add a pre-scene alignment phase that prepares inventory and dynamic continuity state for the next scene before writing starts.

## Key Decisions
- `state_patch` is authoritative for state change. If a value is not updated in patch, it is treated as unchanged.
- No deterministic UI/prose extraction will be used to synthesize mechanic updates.
- Pre-scene alignment is LLM-driven and can update both inventory posture and dynamic continuity state.
- Dynamic continuity must support unknown future mechanic families without schema redesign.

## Scope
- New/updated phase behavior: planning, preflight alignment, continuity pack, write, state repair, lint, repair.
- Prompt hardening across all LLM-facing templates touching state.
- Schema/validation updates for dynamic continuity objects and update operations.
- Parser/normalizer updates for robust canonical patch handling.
- Tests, logging, and rollout controls.

## Out of Scope
- Deterministic RPG simulation engine.
- Genre-specific pipeline forks.
- Converting prose into canonical state outside LLM patch outputs.

## Naming and Contract
### Canonical state containers
- Character scope: `character_continuity_system_state`
- Global/book scope: `global_continuity_system_state`

### Canonical state patch updates
- Character updates: `character_continuity_system_updates`
- Global updates: `global_continuity_system_updates`

### Update operation shape
- `set` for authoritative replacement/update of keys.
- `delta` for numeric adjustments.
- `remove` for explicit key deletion.
- `reason` for human/audit explanation.

### Resolution rule
- If both `set` and `delta` target the same key in one update object, `set` wins.

## Pipeline Changes
### New phase: `scene_state_preflight`
- Runs after `plan_scene`, before `continuity_pack`.
- Inputs:
  - Current scene card.
  - Cast IDs for this scene.
  - Last valid persisted character states for cast.
  - Last valid global continuity state.
  - Previous scene prose/context when available.
  - Last appearance scene prose/context for cast members not present in immediate prior scene.
- Outputs:
  - Canonical `state_patch` updates for inventory posture and dynamic continuity readiness for this scene.
  - No prose output.

### Scene context sourcing rules
- Chapter 1 scene 1:
  - No previous-scene prose exists.
  - Preflight uses outline/scene-card + existing character/global state only.
- Character first appearance in book:
  - No prior appearance prose included.
  - Preflight establishes initial scene-valid posture/state.
- Character reappears after absence:
  - Include latest prior appearance scene prose/context for that character.
- Immediate scene transitions:
  - Include prior scene prose/context and current state to align transition posture.

### Existing phases (revised responsibilities)
- `plan_scene`:
  - Declares expected mechanic families and state focus for the scene.
- `continuity_pack`:
  - Summarizes only persisted canonical state + summaries; does not invent source-of-truth mechanics.
- `write_scene`:
  - Must emit prose + patch; patch contains all mechanic changes introduced in prose/UI.
- `state_repair`:
  - Must repair invalid/missing patch structure and reconcile with persisted state contracts.
  - Does not invent from deterministic extraction; it is an LLM reconciliation pass.
- `lint_scene`:
  - Verifies consistency and contracts.
  - Flags drift; does not auto-create missing mechanic updates from prose/UI.
- `repair_scene`:
  - Final LLM repair of prose + patch coherence when lint fails.

## Prompt Hardening Plan (All LLM Phases)
### Common hard rules
- State ownership rule:
  - Any mechanic introduced or changed in scene output must be represented in canonical patch updates.
- Unchanged fallback rule:
  - If mechanic value is omitted from patch updates, it is assumed unchanged from persisted state.
- Dynamic family rule:
  - New mechanic families are allowed and must be written into continuity system state under stable keys.
- Transition posture rule:
  - Inventory and carried/holstered/worn/container state must be scene-appropriate, not merely scene-legal.

### Template updates required
- `resources/prompt_templates/system_base.md`
- `resources/prompt_templates/plan.md`
- `resources/prompt_templates/continuity_pack.md`
- `resources/prompt_templates/write.md`
- `resources/prompt_templates/state_repair.md`
- `resources/prompt_templates/lint.md`
- `resources/prompt_templates/repair.md`
- `resources/prompt_templates/output_contract.md`

### Genre examples requirement
- Include high-detail examples showing dynamic continuity for:
  - LitRPG stats, resources, titles, passives, cooldowns, status effects.
  - DnD-style sheet fragments, class/subclass, spell slots, conditions.
  - Isekai/fantasy progression systems and discovered rules.
- Emphasize example intent:
  - Demonstrate extensible structure, not fixed schema families.

## Schema and Validation Plan
### `state.schema.json`
- Keep `character_continuity_system_state` and `global_continuity_system_state` as permissive dynamic objects.
- Keep inventory/container schemas intact.
- Preserve compatibility mirrors only if actively needed; otherwise deprecate with clear migration window.

### `state_patch.schema.json`
- Require canonical update keys for preflight/write/repair outputs.
- Validate update items with `set|delta|remove|reason` operation shape.
- Allow unknown nested keys in `set` payloads for dynamic families.

### `scene_card.schema.json`
- Add optional scene state focus fields:
  - expected mechanic domains
  - expected inventory posture constraints

## Parser and Normalizer Plan
- Normalize legacy patch keys into canonical keys.
- Preserve user prompt refinements already present.
- Remove deterministic mechanic synthesis from prose/UI.
- Keep deterministic structural repair only:
  - missing arrays/objects shape fixes
  - scalar-to-list coercions where contract allows
  - canonical key migration
- If patch is semantically missing required state changes, route to LLM state repair, not deterministic extraction.

## Cast-Aware State Handling Plan
- All state checks and phase inputs operate over `cast_present_ids` for the current scene.
- Preflight updates are scoped to cast + global state only.
- Lint comparisons for mechanic ownership/mismatch resolve against relevant cast member and global state.
- Multi-character ambiguity handling:
  - prefer explicit owner keys in UI/system blocks.
  - if owner is ambiguous, lint warns with actionable remediation and triggers repair path when policy requires.

## Inventory and Transition Alignment Plan
- Preflight explicitly validates and aligns:
  - hand occupancy
  - equipped vs stowed posture
  - container placement
  - location-appropriate carry status
- Example target behavior:
  - combat scene can end with sword in hand.
  - next town/social scene preflight can transition sword to sheath/pack if scene card implies non-combat posture.
- This alignment is authored by LLM patch with reason notes.

## Failure Policy
- Missing mechanic update in patch:
  - treat as unchanged.
  - lint can fail if prose claims change but patch does not.
- Invalid patch structure:
  - deterministic structural normalize first.
  - if still invalid, run `state_repair` LLM pass.
- Persistent contradiction after repair:
  - fail scene and stop run with actionable message.

## Logging and Observability
- Every phase log must include: book/chapter/scene scope + phase + model + key-slot.
- Preflight logs must persist:
  - inputs summary (which prior prose/context was included)
  - canonical patch output
  - normalized patch result
- Lint logs must classify violations:
  - ownership missing
  - mismatch
  - transition posture mismatch
  - dynamic family missing in patch

## Risks and Mitigations
- Risk: token cost increase from preflight context.
- Mitigation: pass only scoped prior context (immediate prior + last appearance for cast) and summaries.

- Risk: model under-updates patch fields.
- Mitigation: stricter output contract + state_repair escalation + stop-on-contradiction policy.

- Risk: dynamic keys fragment due to alias churn.
- Mitigation: canonical naming guidance + key alias map + lint warning on alias proliferation.

- Risk: over-constrained prompts reduce prose quality.
- Mitigation: keep mechanics constraints in state contract sections; preserve voice/style sections unchanged.

## Stories and Definition of Done
### Story 1: Canonical Contract Lock
- Update schemas and validators to enforce canonical continuity update operations.
- DoD:
  - canonical keys validated.
  - legacy keys normalized.
  - no deterministic prose->mechanic synthesis remains.

### Story 2: Preflight Phase Implementation
- Add `scene_state_preflight` phase with dedicated model/api settings.
- Wire into run loop after planning and before continuity pack.
- DoD:
  - preflight runs each scene.
  - chapter 1 scene 1 and first appearance edge cases handled.
  - preflight patch is applied before continuity generation.

### Story 3: Prompt Hardening Across Phases
- Update all templates listed above with authoritative-state rules and dynamic family guidance.
- DoD:
  - write/repair/state_repair explicitly require mechanic changes in patch.
  - planning/preflight include expected mechanic domains.
  - existing timeline/state/inventory quality constraints preserved.

### Story 4: Cast-Aware Lint + Repair Routing
- Make lint and checks cast-aware with explicit owner handling.
- Route semantic omissions to LLM repair instead of brittle deterministic inference.
- DoD:
  - multi-character false warnings reduced.
  - ambiguous ownership produces actionable lint output.

### Story 5: Transition Inventory Alignment
- Add preflight inventory posture checks and adjustment guidance.
- DoD:
  - transition scenes correct posture mismatches through preflight patch.
  - no implicit teleporting/hand-state drift across scene boundaries.

### Story 6: Logging + QA Harness
- Add scoped logging for preflight and state ownership decisions.
- Expand tests for structural and semantic contracts.
- DoD:
  - logs show phase-level state decisions.
  - regression tests cover known chapter-1 failure classes.

## Test Plan
### Unit tests
- canonical key normalization from legacy patch shapes.
- update operation precedence (`set` over `delta`).
- dynamic family payload acceptance (titles, resources, custom mechanics).
- cast-aware owner resolution behavior.

### Integration tests
- full scene flow with preflight -> continuity -> write -> state_repair -> lint -> repair.
- chapter 1 scene 1 no-prior-prose path.
- character reappearance with last-appearance context path.
- transition posture correction case (combat to town).

### Regression tests
- preserve existing timeline lock, milestone uniqueness, no-recap behavior.
- ensure prompt changes do not remove existing accepted user refinements.

## Rollout Strategy
- Phase 0: schema + parser + prompts behind feature flag.
- Phase 1: enable preflight for one test book (`criticulous_b1`).
- Phase 2: evaluate drift reduction and false-positive rate.
- Phase 3: make preflight default; keep rollback flag for one release window.

## Acceptance Criteria
- Mechanic changes persist only through canonical patch updates.
- Dynamic continuity captures stats, skills, titles, and unknown future families without schema churn.
- Inventory posture aligns scene-to-scene via preflight.
- Multi-character scenes avoid first-character-only assumptions.
- No deterministic UI/prose fallback is required for mechanic persistence.
