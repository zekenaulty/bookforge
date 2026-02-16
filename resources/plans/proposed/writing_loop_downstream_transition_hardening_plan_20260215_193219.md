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

## Reviewer Cross-Check Adoption (Current Refinement)
Adopted and encoded in this plan:
1. Mechanical definitions for opening-span extraction, semantic adjudication rubric, and deterministic evidence payload schema (WS0/WS1).
2. Explicit strictness precedence, single resolver ownership, and required run-report logging of resolved strictness source (WS0/WS2).
3. Canonical-key requiredness policy and explicit fail behavior for missing required outline fields (WS0/WS3).
4. Stable provenance hash inputs and normalizer-version capture to prevent false reuse invalidation (WS4).
5. Deterministic location migration algorithm and authoritative ID/label responsibilities (WS5).
6. Three-tier unknown world-key policy with explicit defaults and reporting (WS8 + decision register).
7. Shared normalization/hash function requirement across runtime, hashing, and report emission (WS9).
8. Canonical seam end-to-end regression fixture requiring lint failure then repair compliance (WS10).
9. Post-WS3 repair prompt alignment touch-up pass in execution order (execution sequence update).
10. Decision register with defaults, rationale, encoding location, and test mapping (resolved decisions section).

## Deprecated Story Group (Token Handshake Transition Validation)
Deprecated by user direction:
1. Token/anchor handshake validation as a primary transition gate.
2. Exact phrase-or-anchor substring matching as pass/fail authority for bridge validity.
3. Any story that treats a single token string in opening prose as sufficient bridge proof.

Replacement policy:
1. Transition validity is judged by narrative bridge quality criteria (semantic adjudication with structured evidence).
2. Deterministic checks remain for structure and policy wiring (bridge required, opening-span extraction, strictness resolution, report integrity), not token phrase matching.
3. Legacy `transition_*_anchors` fields remain compatibility-only metadata until schema migration completes.

## User Concern Record and Adopted Policy Response
User concern captured:
1. User expressed that a rigid key-phrase-only gate is likely to produce avoidable failures.
2. User explicitly stated higher trust in LLM semantic judgment than pure substring enforcement.
3. User requested that transition compliance be enforced as system-level instruction, not advisory phase text.

Adopted response in this plan:
1. Transition realization requirement is elevated into system-level rules as a hard instruction.
2. Strict mode behavior is hard-blocking when semantic adjudication returns invalid transition realization.
3. Non-strict mode uses semantic adjudication with deterministic reporting:
   - deterministic preprocessing builds bridge-required context and opening-span extraction,
   - lint model adjudicates bridge quality against a fixed rubric,
   - valid/invalid judgment is accepted only when schema-valid evidence is returned,
   - non-strict can downgrade severity to warning with explicit rationale and evidence.
4. Any semantic override must be explicit in run artifacts with rationale and evidence excerpt.
5. No silent pass behavior is allowed from semantic adjudication.

## Scope
In scope:
1. Lint code-orchestrated seam enforcement.
2. Transition strictness propagation and policy wiring.
3. System-level transition instruction hardening for write/repair/lint phases.
4. Planner canonical-field lock behavior.
5. Scene-card reuse invalidation using provenance.
6. Canonical location identity handling across preflight, state apply, and durable filtering.
7. Repair transition contract parity with write.
8. Scene card schema tightening for transition/link fields.
9. World update key guardrails.
10. Runtime prompt sync integrity checks.
11. Test coverage for all above.

Out of scope:
1. New story quality heuristics unrelated to transition/location.
2. Full rework of continuity model families.
3. Outline pipeline architecture changes beyond downstream integration.

## Success Criteria
Release is complete only when all conditions are true:
1. Lint can emit `transition_bridge_missing` via code-orchestrated semantic adjudication with structured schema-validated evidence.
2. Strictness behavior is explicit and reproducible (no hidden "strict mode" language ambiguity).
3. Scene cards for resumed runs are invalidated when outline provenance changes.
4. World location identity uses canonical ID flow through downstream state handling.
5. Repair can reliably respond to transition-seam lint issues with explicit contract guidance.
6. Schema disallows malformed transition/link payloads that previously passed.
7. Tests cover transition adjudication contracts, canonicalization lock, provenance invalidation, and location identity.
8. System-level prompt rules contain explicit non-optional transition realization requirements.
9. Non-strict semantic adjudication path (if used) is fully auditable and cannot silently suppress deterministic failures.

## Workstream Matrix
| Workstream | Risk | Objective |
|---|---|---|
| WS0 | Medium | Establish implementation guardrails and sequencing |
| WS1 | Critical | Add semantic bridge-quality lint checker (code-orchestrated, schema-validated) |
| WS2 | High | Wire strictness and hybrid transition policy into lint/repair/system prompts and runtime |
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
5. Freeze bridge-evaluator constants:
   - opening span mode,
   - opening span bounds,
   - semantic rubric version,
   - adjudication evidence payload shape for transition issues.
6. Freeze canonical-key requiredness policy for WS3:
   - `required_by_applicability` keys,
   - `optional_if_present` keys.
7. Freeze status and report visibility contract:
   - resolved strictness value + source always emitted in run report,
   - report contains deterministic checker constants used in run.
8. Freeze transition validation mode defaults:
   - strict mode uses semantic adjudication with hard blocking on invalid verdict,
   - non-strict mode uses semantic adjudication with downgrade policy and mandatory audit evidence.

### Acceptance
1. Implementation order and dependencies documented and agreed.
2. No workstream starts without explicit touchpoint list and test target.
3. Deterministic constants and requiredness policy are encoded in one authoritative location.
4. Run report field contract is finalized before WS1/WS2 implementation.
5. Transition validation mode defaults are frozen and documented before WS1/WS2 implementation.

### Deterministic Defaults (Locked in WS0)
1. Opening span definition:
   - Parse prose paragraphs by normalized newlines (`\r\n` -> `\n`), split on blank-line boundaries.
   - Use first `2` non-empty paragraphs as opening span.
   - If fewer than `2` paragraphs exist, use available non-empty paragraphs.
   - If paragraph parsing yields no non-empty paragraph, fallback to first `900` characters.
2. Semantic adjudication rubric (v1):
   - bridge-required determination is provided from scene metadata (no model inference for requirement),
   - opening-span bridge must include explicit connective action (not recap-only),
   - when location changes, adjudication must confirm explicit movement/transfer realization,
   - adjudication must confirm POV-consistent transition realization,
   - hard-cut justification is required when handoff mode is discontinuous and bridge realization is minimal.
3. Transition issue evidence payload schema:
   - `opening_span_start_index`
   - `opening_span_end_index`
   - `opening_span_excerpt`
   - `bridge_required` (boolean)
   - `semantic_verdict` (`valid`|`invalid`)
   - `semantic_rationale` (string)
   - `evidence_quotes` (array, max 3 short excerpts)
   - `pov_consistency` (`pass`|`fail`)
4. Strictness precedence chain default:
   - `--transition-strict` explicit CLI flag (highest),
   - latest outline policy report strictness,
   - scene-card strictness hint,
   - `BOOKFORGE_LINT_MODE` mapping fallback (lowest).
5. Required-by-applicability canonical keys for WS3:
   - `location_start_id`, `location_end_id`
   - `handoff_mode`, `constraint_state`
   - `transition_in_text`
6. Optional-if-present canonical keys for WS3:
   - `location_start_label`, `location_end_label`
   - `transition_out_text`
   - `consumes_outcome_from`, `hands_off_to`
   - `seam_score`, `seam_resolution`
7. Transition validation mode defaults:
   - strict mode: invalid semantic verdict is authoritative and non-overridable.
   - non-strict mode: semantic invalid verdict may be downgraded only when evidence is explicit and logged.

### Span Glossary (Locked Terms)
1. `opening span`
   - The deterministic prose window inspected for transition-entry realization.
   - Computed using the WS0 opening-span algorithm (first 2 non-empty paragraphs, fallback first 900 chars).
2. `evidence span`
   - The exact indexed slice used by lint evidence reporting for transition checks.
   - Encoded as `opening_span_start_index`, `opening_span_end_index`, and `opening_span_excerpt`.
3. `closing span`
   - Reserved term for future end-of-scene transition-out enforcement.
   - Not active in WS1; included here to prevent term drift in later plan revisions.

## WS1 - Semantic Transition Bridge Evaluator (Code-Orchestrated)
### Objective
Implement code-orchestrated semantic seam validation in lint tripwires, with clear criteria for `transition_bridge_missing`, and enforce schema-validated adjudication evidence.

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
   - Input: `scene_card`, `prose`, strictness bool, adjudication client/context.
   - Logic:
     - Determine if discontinuity expected:
       - `handoff_mode != direct_continuation`, or
       - canonical location start/end indicate movement/handoff.
     - Build deterministic opening-span extraction payload and bridge-required context.
     - Call lint semantic adjudication contract (`transition_bridge_judgment_v1`) with strict JSON response schema.
     - Emit `transition_bridge_missing` when semantic verdict is invalid with structured evidence.
2. Merge deterministic transition issues in lint phase combined issues path.
3. Ensure severity is deterministic from explicit strictness input and verdict policy, not model-selected severity text.
4. Keep prompt instruction aligned with code behavior (no policy mismatch).
5. Emit checker settings in lint output/report payload:
   - opening span mode and bounds,
   - semantic rubric version,
   - strictness resolved value and source.
6. Emit semantic-adjudication payload for all bridge-required scenes:
   - scene ref,
   - bridge-required reason,
   - opening span excerpt,
   - semantic verdict,
   - semantic rationale.

### Acceptance
1. `transition_bridge_missing` is emitted only through schema-valid adjudication results.
2. Strict/non-strict severity for this issue is code-controlled.
3. Prompt and code wording do not conflict.
4. Evidence payload includes opening-span indices and semantic rationale fields.
5. Two identical inputs with identical model output produce identical issue evidence.
6. Adjudication payload is deterministic and complete for model review.

### Residual Risk
Medium after implementation (semantic variance remains; mitigated by strict schema, rubric versioning, and report visibility).

## WS2 - Strictness Policy Wiring (Lint and Repair)
### Objective
Remove implicit strictness in prompt text, enforce system-level transition rules, and pass explicit policy flags into runtime prompt inputs.

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
5. `resources/prompt_blocks/phase/system_base/global_system_rules.md`
6. `resources/prompt_templates/system_base.md`
7. `workspace/books/<book_id>/prompts/system_v1.md` (after template sync/compile)

Docs:
1. `docs/help/run.md`

Tests:
1. `tests/test_runner_outline_gate.py` (extend strictness interactions if needed)
2. `tests/test_lint_transition_tripwires.py` (severity mode tests)

### Tasks
1. Add explicit `transition_strict` prompt variable to lint and repair prompt render inputs.
2. Add explicit `transition_validation_mode` variable:
   - `semantic_hard_block` (strict),
   - `semantic_advisory` (non-strict).
3. Update lint prompt wording to reference explicit fields (not unnamed "strict transition mode").
4. Add system-level transition rule text in global system prompt blocks:
   - required transition realization in opening span for discontinuous handoffs,
   - no advisory phrasing for this rule.
5. Ensure lint model emits semantic adjudication output for every bridge-required scene in both modes.
6. Ensure repair receives mode context when deciding whether transition fixes are required vs advisory.
7. Keep fallback behavior deterministic if policy input is absent.
8. Add one strictness resolver function used by runner and phases (no duplicate resolution logic).
9. Persist strictness and validation-mode diagnostics in run artifacts:
   - `transition_strict_resolved`,
   - `transition_strict_resolution_source`,
   - `transition_validation_mode_resolved`,
   - `transition_validation_mode_source`.

### Acceptance
1. Prompt sees explicit strictness flags in render context.
2. Lint and repair behavior is consistent with run policy and outline pipeline report semantics.
3. No silent severity downgrades for transition issues due to missing prompt context.
4. Run report and phase history include strictness resolved value and source on every run.
5. System prompt includes explicit hard transition rule language for discontinuity cases.
6. Non-strict semantic adjudication cannot silently clear invalid verdicts without explicit evidence.

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
   - `transition_in_text`
   - `transition_out_text` when present in outline
   - `consumes_outcome_from`, `hands_off_to` when present
   - `seam_score`, `seam_resolution`
2. Normalize with outline-first behavior for canonical keys.
3. Optionally record mismatch diagnostics if model differs from outline source.
4. Ensure schema validation remains strict post-normalization.
5. Enforce missing-key behavior:
   - For `required_by_applicability` keys missing from `outline_window.current`, hard-fail planning with reason code `PLAN_MISSING_CANONICAL_OUTLINE_FIELD`.
   - Model-supplied replacement is not allowed for required canonical keys.
   - For `optional_if_present` keys, omit if absent in outline.
6. Emit canonical-lock diagnostics in plan artifacts:
   - keys locked from outline,
   - keys omitted as optional,
   - keys causing hard failure.

### Acceptance
1. Canonical keys in scene card cannot drift from outline source during plan normalization.
2. Optional keys still obey "omit when not present" policy.
3. Required canonical-key absence is deterministically blocked with explicit reason code.

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
   - normalizer version
   - scene-card schema hash
2. Update `_existing_scene_card` reuse logic to validate provenance against current runtime state.
3. If provenance mismatch, force replan (do not reuse).
4. Add debug log entries for reuse accept/reject reasons.
5. Standardize provenance hash inputs:
   - newline normalization (`CRLF` -> `LF`),
   - stable include resolution order for composed templates,
   - normalized-content hash function shared with WS9.

### Acceptance
1. Resume cannot reuse scene cards from incompatible outline/template provenance.
2. Replan happens automatically with clear operator-visible reason.
3. Equivalent content with formatting-only differences does not trigger false invalidation.

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
5. Implement deterministic migration precedence for legacy states:
   - if `scene_card.location_end_id` exists, set `world.location_id` from scene card,
   - else if existing `world.location_id` exists and is valid, preserve it,
   - else map legacy `world.location` label through active `location_registry` aliases,
   - else emit explicit failure (`STATE_LOCATION_ID_UNRESOLVED`) and stop.
6. Define write policy for legacy alias:
   - once `world.location_id` is present, `world.location` becomes derived display alias and is no longer authoritative.

### Acceptance
1. Preflight and downstream state application no longer normalize world location solely via `scene_target` label.
2. Durable filtering behavior remains stable across reruns and scene transitions.
3. Legacy state migration behavior is deterministic and test-covered.

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
   - transition evidence acceptance criteria (semantic bridge quality rubric)
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
2. Deprecate `transition_in_anchors` and `transition_out_anchors` from enforcement-critical schema requirements (retain compatibility-only support during migration window).
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
4. Implement explicit unknown-key policy modes:
   - `error` (default for strict/CI; hard fail),
   - `warn_drop` (default for exploratory local override; drop key and continue),
   - `allow` is not supported.
5. Add operator-facing controls and report fields:
   - active unknown-key policy in run report,
   - list of dropped/rejected keys with source phase.
6. Define allowlist expansion workflow:
   - unknown keys cannot become accepted via model output,
   - allowlist grows only through code/schema change and test updates.

### Acceptance
1. Unknown world keys cannot persist silently.
2. State remains schema-valid and deterministic after patch application.
3. Policy behavior is explicit, reproducible, and visible in reports.

## WS9 - Runtime Prompt Sync Guardrail
### Objective
Reduce drift risk between source prompt templates and book-local template copies.

### Touchpoints
Code:
1. `src/bookforge/pipeline/prompts.py`
2. `src/bookforge/runner.py`
3. `src/bookforge/cli.py` (optional command flag for strict sync)
4. `src/bookforge/pipeline/prompt_normalization.py` (new shared normalization/hash helper)

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
4. Use one shared normalization/hash function for:
   - runtime prompt loading normalization,
   - prompt hash generation,
   - reported template hash emission.
5. Include resolved sync policy and mismatch list in run report.

### Acceptance
1. Operators can detect and prevent stale prompt-template drift before execution.
2. Check behavior is documented and test-covered.
3. Hashing and normalization are consistent across runtime, reports, and tests.

## WS10 - Test Plan, Audit Gates, and Signoff
### Objective
Establish minimal but decisive coverage for the new contract behavior.

### Touchpoints
Tests:
1. `tests/test_lint_transition_tripwires.py` (new)
2. `tests/test_repair_transition_contract.py` (new)
3. `tests/test_resume_scene_card_provenance.py` (new)
4. `tests/test_state_location_identity.py` (new)
5. `tests/test_e2e_transition_seam_regression.py` (new)
6. `tests/test_lint_transition_semantic_adjudication.py` (new)
7. Existing test updates:
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
6. Add canonical seam regression fixture:
   - discontinuity-required scene card (`handoff_mode != direct_continuation`, start/end location IDs differ),
   - prose opening lacks valid bridge realization,
   - lint semantic adjudication returns invalid and emits `transition_bridge_missing`,
   - repair must produce compliant bridge realization while maintaining patch/schema constraints.
7. Add strict vs non-strict adjudication fixture pair:
   - strict mode: invalid semantic verdict remains hard error.
   - non-strict mode: invalid semantic verdict may downgrade only with explicit evidence payload and rationale.

### Acceptance Gates
Gate A - Unit contracts:
1. New/updated tests pass locally.

Gate B - Prompt/code alignment:
1. Transition contract language is consistent in lint/write/repair/preflight prompts.

Gate C - Runtime behavior:
1. Scene-card reuse invalidation works.
2. Lint emits schema-evidenced `transition_bridge_missing` where expected.
3. Strictness behavior is predictable and documented.

Gate D - Audit output:
1. No unresolved high-risk findings remain in transition/location downstream path.

## Detailed Task Execution Contracts (Handling, Changes, Why, Ramifications)
This section hardens execution by defining exactly how each workstream is implemented, what changes are expected, why they are required, and what downstream effects to expect.

### WS0 - Guardrails, Sequencing, and Change Control
Handling:
1. Execute WS0 as a pre-implementation lock step before code changes.
2. Freeze canonical field ownership and strictness precedence in writing.
3. Publish a dependency map so no downstream WS starts with ambiguous assumptions.

What will change:
1. This plan will be treated as execution authority for scope and sequencing.
2. Cross-plan references will be updated to prevent contradictory behavior between outline and writing loop plans.

Why:
1. Prevents parallel edits from reintroducing model-first canonical drift.
2. Reduces rework from mid-stream policy reversals.

Ramifications:
1. Slight front-loaded planning overhead.
2. Faster implementation velocity after WS0 because decision churn is reduced.
3. Lower regression risk in WS3, WS4, and WS5 where coupling is highest.

### WS1 - Semantic Transition Bridge Evaluator (Code-Orchestrated)
Handling:
1. Implement seam detection in deterministic tripwire code, not prompt-only analysis.
2. Evaluate opening-span transition quality with schema-bound semantic adjudication.
3. Drive severity from explicit strictness input in code.
4. Produce deterministic adjudication payload for every bridge-required scene.

What will change:
1. `src/bookforge/pipeline/lint/tripwires.py` gains transition seam checker logic.
2. `src/bookforge/phases/lint_phase.py` merges deterministic transition issues into combined lint issues.
3. `resources/prompt_templates/lint.md` and lint blocks are aligned to code behavior to avoid contract drift.
4. New tests validate strict and non-strict issue behavior.
5. Lint artifacts include adjudication candidates and evidence payload for non-strict mode.

Why:
1. Current seam enforcement is not deterministic and can silently miss teleport seams.
2. Transition gating must be reproducible and auditable across runs.
3. User concern on brittle phrase-only enforcement is addressed by deprecating token handshake validation and using semantic bridge quality adjudication with audit trail.

Ramifications:
1. More seam violations will surface initially (expected).
2. Repair cycle volume may rise until prompt compliance stabilizes.
3. Risk of semantic variance across LLM responses; mitigated by strict response schema, rubric versioning, and report evidence requirements.
4. Non-strict runs may have additional lint-model adjudication cost.

### WS2 - Strictness Policy Wiring (Lint and Repair)
Handling:
1. Wire strictness flags explicitly into prompt render payloads.
2. Stop relying on prompt prose that references unnamed strict modes.
3. Keep strictness resolution deterministic and documented.
4. Enforce system-level transition realization language as hard instruction.

What will change:
1. `src/bookforge/phases/lint_phase.py` and `src/bookforge/phases/repair_phase.py` pass transition strictness fields.
2. `src/bookforge/runner.py` and config helpers resolve strictness precedence.
3. `resources/prompt_templates/lint.md` and `resources/prompt_templates/repair.md` consume explicit mode variables.
4. Help docs are updated with strictness behavior and override semantics.
5. `resources/prompt_blocks/phase/system_base/global_system_rules.md` and compiled system template carry mandatory transition rule text.
6. Lint/repair prompts gain explicit semantic-adjudication contract for non-strict mode.

Why:
1. Prevents mode ambiguity that causes inconsistent severity outcomes.
2. Aligns runtime behavior with plan and operator expectations.
3. Ensures transition rule compliance is anchored in system-level instructions, not optional phase guidance.

Ramifications:
1. Stronger policy consistency across lint and repair.
2. Existing workflows that assumed implicit defaults may need flag updates.
3. Reduced "why did lint mark this warning here but error there" ambiguity.
4. Slightly higher prompt complexity for lint/repair due to explicit adjudication fields.

### WS3 - Planner Canonical Field Lock
Handling:
1. Enforce outline-first canonical keys in plan normalization.
2. Permit model freedom only on non-canonical narrative scaffolding fields.
3. Log mismatches when model output diverges from outline canonical values.

What will change:
1. `src/bookforge/phases/plan.py` canonical key normalization shifts from model-first to outline-first.
2. Planning prompt contract clarifies that canonical fields are locked by outline.
3. Schema validation remains post-normalization to catch malformed values.

Why:
1. Eliminates primary drift path where model reshapes transition/location identity.
2. Ensures outline transition commitments survive into scene cards.

Ramifications:
1. Lower semantic drift and fewer cross-phase contradictions.
2. Possible initial increase in plan-phase hard failures if outline canonical fields are incomplete.
3. Better deterministic debugging because source of truth is explicit.

### WS4 - Resume Reuse Provenance Invalidation
Handling:
1. Stamp scene cards with provenance.
2. Require provenance match before reuse on resume.
3. Force replan automatically when provenance mismatches.

What will change:
1. `src/bookforge/phases/plan.py` writes provenance metadata into scene cards.
2. `src/bookforge/runner.py` validates outline/template/schema provenance in reuse path.
3. Scene card schema is updated if provenance fields are schema-governed.
4. New tests validate reuse accept/reject logic.

Why:
1. Prevents stale scene-card reuse after outline reruns or prompt updates.
2. Restores safety guarantees for iterative refine-and-resume workflows.

Ramifications:
1. More replanning after outline changes (correct behavior).
2. Slight runtime cost increase on resume due to provenance checks.
3. Major reduction in hidden stale-artifact bugs.

### WS5 - Canonical Location Identity Through Preflight and State
Handling:
1. Shift world-location authority to canonical location IDs.
2. Preserve human-readable labels as display metadata only.
3. Add migration-safe fallback for legacy states.

What will change:
1. `resources/prompt_templates/preflight.md` updates world alignment to `scene_card.location_end_id` semantics.
2. `src/bookforge/pipeline/state_apply.py` and `src/bookforge/pipeline/durable.py` prefer canonical IDs for location logic.
3. `schemas/state.schema.json` introduces or formalizes canonical location identity fields.
4. Supporting code in preflight/state patch paths is adjusted for compatibility.

Why:
1. Current label-based location normalization conflicts with ID-driven transition contracts.
2. Durable filtering must key from stable identity, not mutable labels.

Ramifications:
1. Migration complexity for existing state snapshots.
2. Short-term compatibility branch logic until full transition completes.
3. Long-term consistency gain across preflight, durable, lint, and repair.

### WS6 - Repair Prompt Transition Contract Parity
Handling:
1. Mirror write-phase transition obligations in repair instructions.
2. Require targeted fixes when `transition_bridge_missing` is present.
3. Keep repair JSON/state patch constraints unchanged.

What will change:
1. `resources/prompt_templates/repair.md` gains explicit transition realization contract.
2. Repair prompt blocks are updated to include semantic bridge-quality remediation rules.
3. `src/bookforge/phases/repair_phase.py` passes strictness context as needed.
4. New repair transition tests verify compliance path.

Why:
1. Lint findings are ineffective if repair is not instructed with matching contracts.
2. Transition defects must be repairable without manual intervention.

Ramifications:
1. Higher repair effectiveness for seam issues.
2. Potential increase in repair output constraints causing early failures until tuned.
3. Lower recurrence of repeated seam violations across cycles.

### WS7 - Scene Card Schema Tightening
Handling:
1. Tighten schema where fields drive deterministic behavior.
2. Reject malformed link/reference payloads early.
3. Keep regeneration path for legacy cards.

What will change:
1. `schemas/scene_card.schema.json` gets:
   - enum constraints for `handoff_mode` and `constraint_state`,
   - reference pattern constraints for `consumes_outcome_from` and `hands_off_to`,
   - deprecation metadata and compatibility constraints for legacy `transition_*_anchors`.
2. Plan/runtime validation path is updated for stricter schema behavior.
3. Schema tests are expanded for invalid payload rejection.

Why:
1. Permissive schema currently allows invalid-but-accepted transition payloads.
2. Strict schema reduces downstream corrective complexity.

Ramifications:
1. Legacy scene cards may fail validation and require regeneration.
2. Early failure rate may rise initially, then drop as prompts align.
3. Improved determinism and reduced ambiguous downstream behavior.

### WS8 - State World Update Guardrails
Handling:
1. Add explicit allowlist for `world_updates` keys.
2. Deterministically reject or ignore unknown keys per policy.
3. Log all unknown key encounters for audit.

What will change:
1. `src/bookforge/pipeline/state_apply.py` enforces allowed-key handling.
2. `src/bookforge/pipeline/state_patch.py` and related schemas align with allowed key model.
3. New tests cover unknown-key injection and safe merge behavior.

Why:
1. Blind merge is a state-corruption and bloat risk.
2. Guardrails prevent silent persistence of malformed world fields.

Ramifications:
1. Some previously accepted patches will now error or warn.
2. Better state integrity and lower latent corruption risk.
3. Clearer debugging because invalid keys are surfaced immediately.

### WS9 - Runtime Prompt Sync Guardrail
Handling:
1. Add a prompt hash integrity check before critical runs.
2. Compare source and runtime template hashes for protected templates.
3. Expose policy as warn-only or hard-block mode.

What will change:
1. `src/bookforge/pipeline/prompts.py` and `src/bookforge/runner.py` add sync validation.
2. Optional CLI/config wiring exposes strict sync behavior.
3. Help docs describe how to interpret and resolve mismatches.

Why:
1. Prevents runtime from quietly using stale prompt templates.
2. Strengthens compiler-as-source-of-truth discipline.

Ramifications:
1. Additional pre-run checks may block some runs until prompts are synced.
2. Reduced drift risk between intended contracts and executed contracts.
3. Better auditability of prompt provenance.

### WS10 - Test Plan, Audit Gates, and Signoff
Handling:
1. Add targeted deterministic tests first, then run full suite.
2. Run an end-to-end outline -> planning -> lint/repair audit sample before signoff.
3. Block release if any high-risk acceptance gate fails.

What will change:
1. New tests for transition tripwires, provenance invalidation, and location identity.
2. Existing tests are updated for stricter schema and strictness policy behavior.
3. Audit report expectations are formalized as release gate evidence.

Why:
1. This work is highly coupled; unit-only confidence is insufficient.
2. Regression-resistant delivery requires reproducible gate evidence.

Ramifications:
1. CI/runtime may get slower due to additional coverage.
2. Defect discovery shifts earlier (desirable).
3. Higher confidence that transition/location hardening survives future prompt/code iterations.

## Execution Order
Recommended implementation sequence:
1. WS0 guardrails.
2. WS1 deterministic seam checker.
3. WS2 strictness wiring.
4. WS6 repair parity.
5. WS3 planner canonical lock.
6. WS6 prompt alignment touch-up pass after WS3 (examples/contracts synced to post-lock canonical behavior).
7. WS4 provenance invalidation.
8. WS5 location identity normalization.
9. WS8 world update guardrails.
10. WS7 schema tightening.
11. WS9 prompt sync guardrail.
12. WS10 full test and audit signoff.

## Rollback Strategy
If regressions appear:
1. Keep deterministic seam checker behind a temporary strictness toggle.
2. Provenance fail-open warn mode is emergency-only, time-boxed (max 48 hours), and requires a loud banner plus explicit operator override flag.
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

## Decision Register (Resolved Defaults)
### Decision D1 - Canonical World Location Representation
Default:
1. Use structured location identity with:
   - `world.location_id` as canonical source of truth.
   - `world.location_label` as display label.
   - `world.location` retained as compatibility alias during migration window only.

Rationale:
1. ID-first behavior aligns preflight, durable, lint, and repair around stable identity.
2. Display labels remain editable without breaking deterministic gating.

Where encoded:
1. `schemas/state.schema.json`
2. `src/bookforge/pipeline/state_apply.py`
3. `src/bookforge/pipeline/durable.py`
4. `resources/prompt_templates/preflight.md`

How tested:
1. `tests/test_state_location_identity.py`
2. `tests/test_durable_state.py`
3. WS10 end-to-end seam regression fixture.

### Decision D2 - Unknown `world_updates` Key Policy
Default:
1. `error` in strict/CI contexts.
2. `warn_drop` allowed only via explicit local override for exploratory runs.
3. `allow` mode is not supported.

Rationale:
1. Prevents silent state drift and key injection from model output.
2. Preserves controlled experimentation without normalizing risky behavior.

Where encoded:
1. `src/bookforge/pipeline/state_apply.py`
2. `src/bookforge/pipeline/state_patch.py`
3. `schemas/state_patch.schema.json` (if tightened)
4. `docs/help/run.md`

How tested:
1. `tests/test_state_world_updates_guardrails.py`
2. `tests/test_state_summary.py`
3. `tests/test_state_rollups.py`

### Decision D3 - Prompt Sync Guardrail Default
Default:
1. Hard block on critical template hash mismatch before run.
2. Explicit override flag required to proceed when mismatch is acknowledged for testing.

Rationale:
1. Ensures runtime cannot silently execute stale prompt contracts.
2. Maintains compiler/source-of-truth discipline under iterative edits.

Where encoded:
1. `src/bookforge/pipeline/prompts.py`
2. `src/bookforge/runner.py`
3. `src/bookforge/cli.py` (override flag surface)
4. `docs/help/run.md`

How tested:
1. `tests/test_prompt_hashing.py`
2. `tests/test_prompt_registry.py`
3. `tests/test_runner_outline_gate.py` (override interaction coverage).

### Decision D4 - Transition Validation Mode Default
Default:
1. Strict mode: semantic adjudication is required and hard-blocking on invalid verdict.
2. Non-strict mode: semantic adjudication remains required for bridge-required scenes, with downgrade policy for invalid verdicts.
3. Semantic adjudication may downgrade severity only with explicit evidence and rationale in run artifacts.
4. Token/anchor handshake checks are deprecated and cannot serve as primary pass/fail authority.
5. Semantic adjudication cannot silently pass without schema-valid evidence payload.

Rationale:
1. Incorporates explicit user preference to trust semantic judgment over token phrase matching.
2. Removes low-value token handshake false failures from transition validation.
3. Keeps auditability by requiring schema-valid evidence and explicit severity policy.

Where encoded:
1. `src/bookforge/phases/lint_phase.py`
2. `src/bookforge/phases/repair_phase.py`
3. `src/bookforge/runner.py`
4. `resources/prompt_blocks/phase/system_base/global_system_rules.md`
5. `resources/prompt_templates/lint.md`
6. `resources/prompt_templates/repair.md`

How tested:
1. `tests/test_lint_transition_tripwires.py`
2. `tests/test_lint_transition_semantic_adjudication.py`
3. `tests/test_e2e_transition_seam_regression.py`
4. `tests/test_schema_validation.py` (anchor deprecation compatibility behavior)

## Definition of Done
This plan is complete when:
1. All WS acceptance criteria pass.
2. High-risk items are reduced to medium-low or lower.
3. Test suite includes deterministic seam/transition coverage and provenance invalidation coverage.
4. Docs reflect strictness and location identity behavior as implemented.
5. System-level transition instruction exists and is validated in compiled templates.
6. Non-strict semantic adjudication outputs are auditable and cannot silently suppress invalid semantic verdicts.
7. Token/anchor handshake validation stories are deprecated and removed from pass/fail gates.
