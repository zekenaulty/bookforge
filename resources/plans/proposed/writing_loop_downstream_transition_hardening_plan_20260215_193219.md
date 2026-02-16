# Writing Loop Downstream Transition Hardening Plan (20260215_193219)

## Purpose
Define a high-detail implementation plan to harden the writing loop after outline transition/location contract upgrades, with explicit downstream touchpoints in code, prompts, schemas, docs, and tests.

This plan focuses on eliminating seam regressions, preventing stale artifact reuse, and restoring deterministic behavior where policy currently depends on model interpretation.

## Baseline Context
This plan assumes prior outline work remains in effect and extends:
1. `resources/plans/proposed/outline_pipeline_refinement_plan_20260214_0615.md`
2. `resources/plans/proposed/outline_pipeline_transition_quality_plan_20260214_1545.md`
3. `resources/plans/proposed/outline_pipeline_strict_json_location_registry_plan_20260215_0510.md`

## Validated Risk Summary
Overall risk: High.

Primary validated risks:
1. No deterministic transition seam checker exists in lint code path.
2. Planner normalization is model-first for canonical transition/location fields.
3. Resume reuse for scene cards is not invalidated by outline provenance.
4. Preflight location normalization is label-driven (`scene_target`) while transition contracts are ID-driven.
5. State world updates accept arbitrary keys and merge blindly.
6. Repair prompt does not mirror write prompt transition realization contract.
7. Scene card schema remains permissive for several transition/link fields.

## Scope
In scope:
1. Lint deterministic seam enforcement.
2. Transition strictness propagation and policy wiring.
3. Planner canonical-field lock behavior.
4. Scene-card reuse invalidation using provenance.
5. Canonical location identity handling across preflight, state apply, and durable filtering.
6. Repair transition contract parity with write.
7. Scene card schema tightening for transition/link fields.
8. World update key guardrails.
9. Runtime prompt sync integrity checks.
10. Test coverage for all above.

Out of scope:
1. New story quality heuristics unrelated to transition/location.
2. Full rework of continuity model families.
3. Outline pipeline architecture changes beyond downstream integration.

## Success Criteria
Release is complete only when all conditions are true:
1. Lint can emit `transition_bridge_missing` from deterministic code, not prompt inference only.
2. Strictness behavior is explicit and reproducible (no hidden "strict mode" language ambiguity).
3. Scene cards for resumed runs are invalidated when outline provenance changes.
4. World location identity uses canonical ID flow through downstream state handling.
5. Repair can reliably respond to transition-seam lint issues with explicit contract guidance.
6. Schema disallows malformed transition/link payloads that previously passed.
7. Tests cover deterministic seam checks, canonicalization lock, provenance invalidation, and location identity.

## Workstream Matrix
| Workstream | Risk | Objective |
|---|---|---|
| WS0 | Medium | Establish implementation guardrails and sequencing |
| WS1 | Critical | Add deterministic seam lint checker |
| WS2 | High | Wire strictness policy into lint/repair prompts and runtime |
| WS3 | High | Lock scene-card canonical fields to outline values |
| WS4 | High | Add provenance-based resume invalidation |
| WS5 | High | Normalize world location through canonical IDs |
| WS6 | Medium | Add transition contract parity in repair prompt |
| WS7 | Medium | Tighten scene card schema for transition/link fields |
| WS8 | Medium | Constrain world update merge behavior |
| WS9 | Medium | Add runtime prompt sync guardrails |
| WS10 | High | Add targeted tests and final audit gates |

## WS0 - Guardrails, Sequencing, and Change Control
### Objective
Define implementation order, feature flags (if needed), and rollback points to avoid partially-applied policy drift.

### Touchpoints
1. `resources/plans/proposed/writing_loop_downstream_transition_hardening_plan_20260215_193219.md` (this file)
2. `resources/plans/proposed/outline_pipeline_transition_quality_plan_20260214_1545.md` (cross-reference updates if needed)
3. `resources/plans/proposed/outline_pipeline_strict_json_location_registry_plan_20260215_0510.md` (cross-reference updates if needed)

### Tasks
1. Freeze canonical field set for scene-card lock behavior.
2. Freeze provenance payload schema for scene-card reuse checks.
3. Define strictness precedence chain:
   - explicit run flag or report policy
   - scene card strictness hint (optional)
   - fallback lint mode
4. Define backward-compat handling for legacy state with `world.location` string only.

### Acceptance
1. Implementation order and dependencies documented and agreed.
2. No workstream starts without explicit touchpoint list and test target.

## WS1 - Deterministic Transition Seam Lint Checker
### Objective
Implement deterministic seam validation in Python lint tripwires, with clear criteria for `transition_bridge_missing`.

### Touchpoints
Code:
1. `src/bookforge/pipeline/lint/tripwires.py`
2. `src/bookforge/pipeline/lint/__init__.py`
3. `src/bookforge/phases/lint_phase.py`

Prompts:
1. `resources/prompt_templates/lint.md`
2. `resources/prompt_blocks/phase/lint/lint_policy_rules_and_inputs.md`
3. `workspace/books/criticulous_b1/prompts/templates/lint.md` (after template sync)

Tests:
1. `tests/test_lint_transition_tripwires.py` (new)
2. `tests/test_lint_helpers.py` (augment if shared helper coverage needed)

### Tasks
1. Add `_transition_bridge_issues(...)` function in tripwires:
   - Input: `scene_card`, `prose`, strictness bool.
   - Logic:
     - Determine if discontinuity expected:
       - `handoff_mode != direct_continuation`, or
       - canonical location start/end indicate movement/handoff.
     - Validate opening-span realization:
       - exact `transition_in_text`, or
       - all `transition_in_anchors` present in opening span.
     - Emit `transition_bridge_missing` with evidence when missing.
2. Merge deterministic transition issues in lint phase combined issues path.
3. Ensure severity is deterministic from explicit strictness input, not model-generated issue severity.
4. Keep prompt instruction aligned with code behavior (no policy mismatch).

### Acceptance
1. `transition_bridge_missing` can be emitted without model help.
2. Strict/non-strict severity for this issue is code-controlled.
3. Prompt and code wording do not conflict.

### Residual Risk
Low-Medium after implementation (text matching ambiguity remains but deterministic scope is explicit).

## WS2 - Strictness Policy Wiring (Lint and Repair)
### Objective
Remove implicit strictness in prompt text and pass explicit policy flags into runtime prompt inputs.

### Touchpoints
Code:
1. `src/bookforge/phases/lint_phase.py`
2. `src/bookforge/phases/repair_phase.py`
3. `src/bookforge/runner.py` (if strictness source is routed from run policy/report)
4. `src/bookforge/pipeline/config.py` (if new config accessors required)

Prompts:
1. `resources/prompt_templates/lint.md`
2. `resources/prompt_templates/repair.md`
3. `resources/prompt_blocks/phase/lint/lint_policy_rules_and_inputs.md`
4. `resources/prompt_blocks/phase/repair/*` relevant files

Docs:
1. `docs/help/run.md`

Tests:
1. `tests/test_runner_outline_gate.py` (extend strictness interactions if needed)
2. `tests/test_lint_transition_tripwires.py` (severity mode tests)

### Tasks
1. Add explicit `transition_strict` prompt variable to lint and repair prompt render inputs.
2. Update lint prompt wording to reference the explicit field (not unnamed "strict transition mode").
3. Ensure repair receives mode context when deciding whether transition fixes are required vs advisory.
4. Keep fallback behavior deterministic if policy input is absent.

### Acceptance
1. Prompt sees explicit strictness flags in render context.
2. Lint and repair behavior is consistent with run policy and outline pipeline report semantics.
3. No silent severity downgrades for transition issues due to missing prompt context.

## WS3 - Planner Canonical Field Lock
### Objective
Prevent model drift in canonical scene-card transition/location fields by locking to `outline_window.current`.

### Touchpoints
Code:
1. `src/bookforge/phases/plan.py`
2. `schemas/scene_card.schema.json` (if required behavior changes schema expectations)

Prompts:
1. `resources/prompt_templates/plan.md`
2. `resources/prompt_blocks/phase/plan/scene_card_prompt_contract_and_schema.md`

Tests:
1. `tests/test_plan_scene.py`
2. `tests/test_outline_transition_policy.py` (if shared assumptions)

### Tasks
1. Define canonical locked key set:
   - `location_start_id`, `location_end_id`
   - `location_start_label`, `location_end_label`
   - `location_start`, `location_end`
   - `handoff_mode`, `constraint_state`
   - `transition_in_text`, `transition_in_anchors`
   - `transition_out_text`, `transition_out_anchors` when present in outline
   - `consumes_outcome_from`, `hands_off_to` when present
   - `seam_score`, `seam_resolution`
2. Normalize with outline-first behavior for canonical keys.
3. Optionally record mismatch diagnostics if model differs from outline source.
4. Ensure schema validation remains strict post-normalization.

### Acceptance
1. Canonical keys in scene card cannot drift from outline source during plan normalization.
2. Optional keys still obey "omit when not present" policy.

## WS4 - Resume Reuse Provenance Invalidation
### Objective
Block stale scene-card reuse after outline reruns or contract changes.

### Touchpoints
Code:
1. `src/bookforge/phases/plan.py`
2. `src/bookforge/runner.py`
3. `src/bookforge/outline.py` (if provenance metadata helpers are centralized)

Schemas:
1. `schemas/scene_card.schema.json` (if provenance fields are schema-governed)

Tests:
1. `tests/test_runner_outline_gate.py` (extend)
2. `tests/test_plan_scene.py` (provenance stamping)
3. `tests/test_resume_scene_card_provenance.py` (new)

### Tasks
1. Stamp scene-card provenance at creation:
   - outline hash
   - outline run id (if available)
   - outline schema version
   - relevant prompt/template hash set
2. Update `_existing_scene_card` reuse logic to validate provenance against current runtime state.
3. If provenance mismatch, force replan (do not reuse).
4. Add debug log entries for reuse accept/reject reasons.

### Acceptance
1. Resume cannot reuse scene cards from incompatible outline/template provenance.
2. Replan happens automatically with clear operator-visible reason.

## WS5 - Canonical Location Identity Through Preflight and State
### Objective
Eliminate label-vs-ID location drift by making canonical location ID the authoritative downstream key.

### Touchpoints
Prompts:
1. `resources/prompt_templates/preflight.md`
2. `resources/prompt_blocks/phase/preflight/transition_gate_world_alignment_and_constraint_enforcement.md`
3. `workspace/books/criticulous_b1/prompts/templates/preflight.md` (after sync)

Code:
1. `src/bookforge/pipeline/state_apply.py`
2. `src/bookforge/pipeline/durable.py`
3. `src/bookforge/phases/preflight_phase.py`
4. `src/bookforge/pipeline/state_patch.py`

Schemas:
1. `schemas/state.schema.json`

Tests:
1. `tests/test_state_location_identity.py` (new)
2. `tests/test_durable_state.py` (augment location identity behavior)

### Tasks
1. Update preflight contract to prefer canonical location ID (`scene_card.location_end_id`) for world alignment.
2. Introduce structured world location fields if required:
   - `world.location_id` (canonical)
   - `world.location_label` (display)
   - retain `world.location` as compatibility alias during migration window.
3. Update durable context to key location comparisons by canonical ID first.
4. Add migration-safe handling for existing states lacking new fields.

### Acceptance
1. Preflight and downstream state application no longer normalize world location solely via `scene_target` label.
2. Durable filtering behavior remains stable across reruns and scene transitions.

## WS6 - Repair Prompt Transition Contract Parity
### Objective
Make repair phase explicitly capable of resolving transition seam violations with the same contract as write/lint.

### Touchpoints
Prompts:
1. `resources/prompt_templates/repair.md`
2. `resources/prompt_blocks/phase/repair/*` relevant files
3. `workspace/books/criticulous_b1/prompts/templates/repair.md`

Code:
1. `src/bookforge/phases/repair_phase.py` (pass explicit strictness/policy fields if needed)

Tests:
1. `tests/test_repair_transition_contract.py` (new)

### Tasks
1. Add repair transition section mirroring write contract:
   - when discontinuity expected, opening realization rules apply
   - transition evidence acceptance criteria (exact text or anchors)
2. Add explicit handling guidance for `transition_bridge_missing`.
3. Keep JSON/state patch constraints unchanged while adding transition guidance.

### Acceptance
1. Repair prompt contains explicit transition reconciliation requirements.
2. Lint -> repair loop can target seam issue class directly.

## WS7 - Scene Card Schema Tightening
### Objective
Prevent malformed transition/link payloads from passing schema validation.

### Touchpoints
Schemas:
1. `schemas/scene_card.schema.json`

Code:
1. `src/bookforge/phases/plan.py` (normalization compatibility)
2. `src/bookforge/runner.py` (runtime validation path already present)

Tests:
1. `tests/test_schema_validation.py`
2. `tests/test_plan_scene.py`

### Tasks
1. Add enums/patterns:
   - `handoff_mode` enum
   - `constraint_state` enum
   - `consumes_outcome_from` / `hands_off_to` `chapter:scene` pattern
2. Add `transition_out_anchors` bounds (3-6) when present.
3. Add conditional constraints where possible without scene-context coupling.

### Acceptance
1. Invalid link/handoff payloads fail schema earlier.
2. Backward compatibility handled for legacy cards via migration or regeneration.

## WS8 - State World Update Guardrails
### Objective
Prevent accidental world-state key injection and uncontrolled drift.

### Touchpoints
Code:
1. `src/bookforge/pipeline/state_apply.py`
2. `src/bookforge/pipeline/state_patch.py`

Schemas:
1. `schemas/state.schema.json`
2. `schemas/state_patch.schema.json` (if world update shape tightening required)

Tests:
1. `tests/test_state_summary.py`
2. `tests/test_state_rollups.py`
3. `tests/test_state_world_updates_guardrails.py` (new)

### Tasks
1. Add allowlist for `world_updates` keys in state apply.
2. Ignore or reject unknown world keys deterministically and log.
3. Align allowed keys with location identity model from WS5.

### Acceptance
1. Unknown world keys cannot persist silently.
2. State remains schema-valid and deterministic after patch application.

## WS9 - Runtime Prompt Sync Guardrail
### Objective
Reduce drift risk between source prompt templates and book-local template copies.

### Touchpoints
Code:
1. `src/bookforge/pipeline/prompts.py`
2. `src/bookforge/runner.py`
3. `src/bookforge/cli.py` (optional command flag for strict sync)

Docs:
1. `docs/help/run.md`
2. `docs/help/outline_generate.md`

Tests:
1. `tests/test_prompt_hashing.py`
2. `tests/test_prompt_registry.py`

### Tasks
1. Add optional strict sync check before run loop:
   - compare normalized-content hashes across critical templates.
2. Decide default mode:
   - warn-only vs hard-fail in strict environments.
3. Emit actionable message when mismatch exists.

### Acceptance
1. Operators can detect and prevent stale prompt-template drift before execution.
2. Check behavior is documented and test-covered.

## WS10 - Test Plan, Audit Gates, and Signoff
### Objective
Establish minimal but decisive coverage for the new contract behavior.

### Touchpoints
Tests:
1. `tests/test_lint_transition_tripwires.py` (new)
2. `tests/test_repair_transition_contract.py` (new)
3. `tests/test_resume_scene_card_provenance.py` (new)
4. `tests/test_state_location_identity.py` (new)
5. Existing test updates:
   - `tests/test_plan_scene.py`
   - `tests/test_runner_outline_gate.py`
   - `tests/test_schema_validation.py`
   - `tests/test_durable_state.py`

Reports:
1. `workspace/books/<book_id>/outline/pipeline_runs/<run_id>/outline_pipeline_report.json`
2. `workspace/books/<book_id>/draft/context/phase_history/...` artifacts

### Tasks
1. Add deterministic unit tests for seam detection with strict and non-strict settings.
2. Add regression test where outline changes invalidate scene-card reuse.
3. Add state-location identity tests proving preflight/state/durable alignment.
4. Add schema tests for new scene-card constraints.
5. Run targeted suites first, then full suite.

### Acceptance Gates
Gate A - Unit contracts:
1. New/updated tests pass locally.

Gate B - Prompt/code alignment:
1. Transition contract language is consistent in lint/write/repair/preflight prompts.

Gate C - Runtime behavior:
1. Scene-card reuse invalidation works.
2. Lint emits deterministic `transition_bridge_missing` where expected.
3. Strictness behavior is predictable and documented.

Gate D - Audit output:
1. No unresolved high-risk findings remain in transition/location downstream path.

## Execution Order
Recommended implementation sequence:
1. WS0 guardrails.
2. WS1 deterministic seam checker.
3. WS2 strictness wiring.
4. WS6 repair parity.
5. WS3 planner canonical lock.
6. WS4 provenance invalidation.
7. WS5 location identity normalization.
8. WS8 world update guardrails.
9. WS7 schema tightening.
10. WS9 prompt sync guardrail.
11. WS10 full test and audit signoff.

## Rollback Strategy
If regressions appear:
1. Keep deterministic seam checker behind a temporary strictness toggle.
2. Keep provenance invalidation in fail-open warn mode only during initial burn-in if needed.
3. Keep world location migration backward compatible for one release window.
4. Do not relax schema changes without explicit decision log entry.

## Operator and Documentation Updates
Required docs updates once implementation lands:
1. `docs/help/run.md`
   - strictness semantics
   - any new ack/bypass behavior
   - prompt sync guardrail behavior
2. `docs/help/outline_generate.md`
   - downstream expectations for transition/location fields
3. Any runbook docs referencing location normalization behavior.

## Outstanding Design Decisions (Must Resolve Before WS5/WS7 Finalization)
1. Canonical world location representation:
   - string ID only, or
   - `{location_id, location_label}` object with compatibility alias.
2. Unknown world key handling policy:
   - reject hard error, or
   - ignore with warning/log.
3. Prompt sync guardrail default:
   - warn, or
   - hard block.

## Definition of Done
This plan is complete when:
1. All WS acceptance criteria pass.
2. High-risk items are reduced to medium-low or lower.
3. Test suite includes deterministic seam/transition coverage and provenance invalidation coverage.
4. Docs reflect strictness and location identity behavior as implemented.

