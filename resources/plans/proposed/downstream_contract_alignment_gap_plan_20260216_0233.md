# Downstream Contract Alignment Gap Plan (Deferred) (20260216_0233)

## Purpose
Define a separate, post-outline-recovery remediation plan for five downstream contract gaps that are currently outside the core multi-phase outline rebuild scope.

This plan exists to prevent loss of signal after outline quality improves, and to enforce the doctrine without mixing these fixes into the active outline recovery stream.

## Execution Status
Status: Deferred.

Execution begins only after the multi-phase outline recovery plan is stable and validated in end-to-end outline runs.

Primary dependency:
1. `resources/plans/proposed/outline_pipeline_rebuild_plan_20260216_0145.md`

## Doctrine Anchor
Locked doctrine:
1. LLM authors and lints.
2. Orchestrator never authors semantic content.
3. Orchestrator never silently discards model-authored data.
4. Orchestrator enforces validated state and deterministic invariants.

## Scope
This plan covers only these five items:
1. Planner propagation gap (`outline_window.current` missing transition/location payload).
2. Lint strictness wiring gap (strict transition policy not explicitly wired in runtime context and no deterministic seam check path).
3. Location ID ownership conflict (orchestrator-owned IDs vs model-required IDs).
4. Prompt/schema mismatch for `end_condition` requiredness.
5. State patch sanitization behavior that can discard unknown LLM keys.

Out of scope for this plan:
1. New outline phases.
2. Character/location promotion phase design.
3. Full entity extraction from prose.
4. Re-architecting the writing loop beyond the listed contract gaps.

## Gap Summary
1. Planner currently cannot reliably carry outline transition/location contract into scene cards.
2. Lint policy text and runtime strictness wiring are not aligned for transition bridge severity behavior.
3. Location ID authority is split across prompt/schema/runtime and creates drift risk.
4. Prompt requires `end_condition`; schema does not enforce it.
5. Sanitization currently filters keys and can violate doctrine on model-authored extensions.

## Workstream 1: Planner Propagation Contract
### Goal
Ensure outline transition/location payload reaches scene-card generation without silent loss or re-derivation drift.

### Touchpoints
1. `src/bookforge/phases/plan.py`
2. `resources/prompt_blocks/phase/plan/scene_card_prompt_contract_and_schema.md`
3. `resources/prompt_templates/plan.md`
4. `schemas/scene_card.schema.json`
5. `tests/test_plan_scene.py`

### Required changes
1. Expand `outline_window.current` payload in planner context to include transition/location fields already present in outline scenes.
2. Define a canonical pass-through key set for planner:
   `location_start_id`, `location_end_id`, `location_start_label`, `location_end_label`, `location_start`, `location_end`, `handoff_mode`, `constraint_state`, `transition_in_text`, `transition_in_anchors`, `transition_out_text`, `transition_out_anchors`, `consumes_outcome_from`, `hands_off_to`, `seam_score`, `seam_resolution`, `hard_cut_justification`, `intentional_cinematic_cut`.
3. Enforce planner normalization policy:
   - For canonical keys present in outline window, preserve values instead of model drift.
   - For canonical keys missing upstream, do not synthesize semantic placeholders.
   - Route to structured failure where required keys cannot be satisfied by contract.
4. Update planner prompt contract wording to match runtime behavior exactly.
5. Add test fixtures proving transition/location fields propagate from outline to scene card.

### Acceptance criteria
1. Scene card includes upstream canonical transition/location values when provided.
2. No planner-authored synthetic transition prose appears during normalization.
3. Planner failures for missing required upstream contract fields are explicit and reason-coded.

## Workstream 2: Lint Strictness Wiring and Seam Enforcement
### Goal
Align lint strictness policy text with runtime configuration and deterministic issue surfacing for transition bridge gating.

### Touchpoints
1. `src/bookforge/phases/lint_phase.py`
2. `src/bookforge/pipeline/lint/tripwires.py`
3. `src/bookforge/pipeline/lint/helpers.py`
4. `resources/prompt_blocks/phase/lint/lint_policy_rules_and_inputs.md`
5. `resources/prompt_templates/lint.md`
6. `tests/test_lint_helpers.py`
7. Add dedicated seam lint tests file if needed.

### Required changes
1. Pass explicit strictness values into lint render context:
   - global lint mode
   - transition strictness mode
2. Implement deterministic transition seam check path in tripwires:
   - emit `transition_bridge_missing` when discontinuity is indicated by scene-card metadata and opening realization evidence is missing.
   - keep deterministic check scoped to contract presence/evidence rules, not semantic prose authoring.
3. Ensure severity mapping follows explicit mode policy, not model guesswork.
4. Ensure lint normalization does not silently downgrade transition severity when strict mode requires error.
5. Add tests for strict and non-strict severity behavior.

### Acceptance criteria
1. Lint prompt always receives explicit strictness context.
2. `transition_bridge_missing` can be emitted deterministically in code path.
3. Strict mode consistently yields error severity for transition bridge violations.

## Workstream 3: Location ID Ownership Unification
### Goal
Resolve ownership conflict by adopting one canonical authority path for location IDs and normalizing all contracts to it.

### Decision to lock
1. Orchestrator owns canonical `LOC_*` ID generation/validation.
2. LLM provides semantic labels and transition semantics.
3. Orchestrator compiles/normalizes IDs from labels and registry.

### Touchpoints
1. `schemas/scene_card.schema.json`
2. `schemas/outline.schema.json`
3. `schemas/outline_location_registry.schema.json`
4. `src/bookforge/phases/plan.py`
5. `src/bookforge/outline.py`
6. `resources/prompt_blocks/phase/plan/scene_card_prompt_contract_and_schema.md`
7. `resources/prompt_blocks/phase/outline_pipeline/phase_03_scene_draft_prompt_contract.md`
8. `resources/prompt_templates/plan.md`
9. Outline phase prompt templates as needed.
10. `tests/test_outline_generate.py`
11. `tests/test_plan_scene.py`

### Required changes
1. Remove contradictory requirements that force model-authored canonical IDs where orchestrator owns ID compilation.
2. Define one normalization point for label-to-ID mapping.
3. Enforce registry membership checks for any compiled IDs.
4. Add explicit failure behavior for unresolved labels instead of placeholder fallback.
5. Keep schema/prompt/runtime aligned on optional vs required ID fields.

### Acceptance criteria
1. No contract contradiction remains about location ID ownership.
2. IDs are deterministic across retries for same labels/registry context.
3. Missing location identity routes to explicit validation failure, not synthetic placeholder.

## Workstream 4: `end_condition` Prompt/Schema Alignment
### Goal
Make `end_condition` requiredness consistent across prompt contracts and schema validation.

### Touchpoints
1. `schemas/outline.schema.json`
2. `resources/prompt_blocks/phase/outline_pipeline/phase_02_section_architecture_prompt_contract.md`
3. `resources/prompt_blocks/phase/outline_pipeline/phase_03_scene_draft_prompt_contract.md`
4. `resources/prompt_templates/outline_phase_02_section_architecture.md`
5. `resources/prompt_templates/outline_phase_03_scene_draft.md`
6. `tests/test_outline_generate.py`

### Required changes
1. Promote section `end_condition` to required in schema.
2. Confirm phase contracts and schema use identical naming and semantics.
3. Add validation test coverage for missing `end_condition`.
4. Keep section-final `end_condition_echo` rule enforced in prompt/validator policy.

### Acceptance criteria
1. Outline with missing section `end_condition` fails schema validation.
2. Prompt contract and schema no longer disagree on requiredness.

## Workstream 5: State Patch Unknown-Key Doctrine Compliance
### Goal
Replace silent unknown-key filtering with preserve-and-route behavior aligned to doctrine.

### Touchpoints
1. `src/bookforge/pipeline/state_patch.py`
2. `schemas/state_patch.schema.json`
3. `resources/prompt_blocks/shared/json_contract/updates_arrays_only_contract_block.md`
4. `resources/prompt_blocks/phase/preflight/durable_update_contracts_and_reason_categories.md`
5. `resources/prompt_templates/preflight.md`
6. `resources/prompt_templates/state_repair.md`
7. `tests/test_state_patch.py`
8. Add new unknown-key routing tests if needed.

### Required changes
1. Remove silent discard behavior for unknown keys in patch sanitization.
2. Introduce unknown-key capture structure with provenance metadata.
3. Route unknown-key classification to LLM repair/classification path.
4. Preserve captured unknown data until classified, mapped, or explicitly escalated.
5. Add gating/reporting behavior so unresolved unknown keys are visible and actionable.

### Acceptance criteria
1. Unknown model-authored keys are preserved and surfaced, not silently dropped.
2. Unknown key handling produces auditable routing artifacts.
3. Classification failures produce explicit attention/failure states.

## Sequencing
Recommended order after outline recovery stabilizes:
1. Workstream 3 (Location ID ownership lock).
2. Workstream 1 (Planner propagation based on locked ownership).
3. Workstream 4 (`end_condition` schema alignment).
4. Workstream 2 (Lint strictness wiring and deterministic seam path).
5. Workstream 5 (Unknown-key doctrine compliance).

Reason:
1. Ownership lock first prevents churn across planner/schema/lint.
2. Planner propagation next ensures downstream phases see real outline contract.
3. Schema alignment avoids false confidence in prompt-only enforcement.
4. Lint strictness then operates on stable payload contracts.
5. Unknown-key compliance last because it impacts wider patch flow and should be isolated after contract stabilization.

## Risks
1. Prompt/schema/runtime drift if only prompt files are updated without matching code and tests.
2. Overly strict required fields may increase retries until upstream contracts are complete.
3. Unknown-key preservation may increase state payload size if not paired with classification lifecycle controls.

## Test Strategy
1. Unit tests per workstream touchpoint.
2. Contract tests for prompt/schema alignment.
3. Integration test:
   - outline with transition/location payload
   - planner card propagation
   - lint transition gate behavior in strict and non-strict
   - state patch unknown-key preservation and routing.

## Definition of Done
1. All five gaps have implemented code+schema+prompt alignment.
2. No silent semantic fallback or silent unknown-key discard remains in covered paths.
3. Tests demonstrate deterministic enforcement plus doctrine compliance.
4. Documentation updated for new strictness/ownership/unknown-key behavior.
