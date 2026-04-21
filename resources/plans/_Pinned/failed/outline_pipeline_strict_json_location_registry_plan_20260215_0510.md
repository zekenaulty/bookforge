# Outline Pipeline Strict JSON + Location Registry Hardening Plan (20260215_0510)

## Purpose
Define the next execution-hardening phase for outline generation so schema-complete JSON, transition identity, and failure visibility are enforced end-to-end.

This plan preserves goals and approved decisions from:
1. `resources/plans/proposed/outline_pipeline_refinement_plan_20260214_0615.md`
2. `resources/plans/proposed/outline_pipeline_transition_quality_plan_20260214_1545.md`

## Carry-Forward Goals (Unchanged)
1. Keep six-phase outline orchestration.
2. Keep compiler/composition as prompt source of truth.
3. Keep rerun and resume behavior.
4. Keep transition-quality enforcement as a primary quality gate.
5. Keep strong non-exact scene-count default and strict mode hard-block behavior.

## Problem Recap
Recent reruns showed this failure class:
1. Outline phase 03 returned transition/location fields, but schema completeness still failed at high volume.
2. Prior normalization policies risked masking missing semantic values.
3. Failure visibility was incomplete because failed runs did not always emit a full outline pipeline report.
4. Book-local template drift can cause runs to execute stale contracts.

## Hard Policy Locks
1. Semantic autofill is forbidden before validation.
2. Deterministic derivation-only autofill is allowed only for direct continuation inheritance.
3. Placeholder identity values are invalid for outline transition/location fields.
4. Location identity is first-class via a registry artifact.
5. Failed outline runs must emit user-visible report artifacts and console summaries.
6. Writing gate is driven by terminal outline status first, then attention state.
7. Retry, stop, and pause outcomes must be classified and surfaced with explicit reason codes.
8. Canonical transition fields are `transition_in_text`, `transition_in_anchors`, `transition_out_text`, and `transition_out_anchors`; legacy aliases are normalized before validation.
9. Orchestrator owns canonical `LOC_*` ID generation; outline models emit location labels, not final IDs.
10. `error_v1` is a first-class structured response with schema and deterministic routing.

## Execution Outcome Matrix (Retry vs Stop vs Pause)
All runs must terminate with one of:
1. `SUCCESS`
2. `SUCCESS_WITH_WARNINGS`
3. `PAUSED`
4. `ERROR`

### Retryable failures (consume attempts, max phase attempts applies)
1. Strict JSON parse failure.
2. Schema missing required keys/types.
3. Placeholder token detected in prohibited fields.
4. Location IDs referenced but missing from location registry.

### Non-retryable failures (stop immediately, user action required)
1. Template drift guard triggered.
2. Resume fingerprint mismatch without explicit override.
3. Exact-scene-count conflict where insertion is required but disallowed by policy.

### Pause conditions (resumable, must still surface strongly)
1. Provider quota/rate-limit/transient upstream availability failures.
2. Optional `--pause-on-attention` mode if configured.

### Mandatory console summary fields (every run)
1. Final status (`SUCCESS | SUCCESS_WITH_WARNINGS | PAUSED | ERROR`).
2. Phase where terminal state occurred.
3. Attempt usage for terminal phase (`N/Max`).
4. Top 3 reason codes.
5. Report artifact path.
6. `ATTENTION ITEMS: <count>` line with top attention reason codes.

### Write gate override policy
1. Writing is blocked whenever latest outline `overall_status` is not `SUCCESS` or `SUCCESS_WITH_WARNINGS`.
2. `--ack-outline-issues` can override attention items only when terminal status is `SUCCESS_WITH_WARNINGS`.
3. `--ack-outline-issues` cannot bypass `PAUSED` or `ERROR`.

## Outline-Specific System Instruction Block (New)
Add this block to outline pipeline prompts (phase 01-06) as outline-only system behavior.

```md
## OUTLINE JSON EXECUTION MODE (STRICT)

You are producing machine-validated JSON for a deterministic pipeline.
Return exactly ONE JSON object and nothing else.

Hard output rules:
- No markdown, no code fences, no commentary, no preamble, no trailing text.
- Use strict JSON only (double quotes, no trailing commas).
- All schema-required keys must be present with correct names and types.
- Never rename schema keys.
- If a required value cannot be derived, return error_v1 JSON only.

Schema discipline:
- chapter_id: sequential integers starting at 1.
- section_id: sequential integers within each chapter.
- scene_id: monotonic chapter-local integer sequence across sections.
- location_start_label and location_end_label are required non-empty location names.
- If a scene is not the first in its chapter, consumes_outcome_from is required (chapter:scene).
- If a scene is not the last in its chapter, hands_off_to and transition_out_text are required.

Placeholder prohibition (hard fail):
- Do not emit placeholder values such as current_location, placeholder, unknown, tbd, here, there, n/a, or empty-string stand-ins for required fields.
- Do not emit synthetic anchors like anchor_1, anchor_2.

Registry discipline:
- If scenes reference characters, top-level characters array is required and must use character_id schema keys.
- If scenes reference threads, top-level threads array is required and must use thread_id schema keys.
- Never use generic id/title substitutes where schema requires character_id/thread_id/label/status.
- Do not invent final LOC_* IDs directly; orchestrator will compile canonical IDs from labels and registry context.

Scope override:
- During outlining, scene-writing rules (state_patch, must_stay_true, prose block formatting) do not apply.
- Timeline Lock does not apply during outlining.
```

## Design Updates (Refined)

### 1) Anti-Masking Validation Order
1. Parse model output JSON.
2. Run strict schema/contract validation against raw parsed payload (label-level contract, no semantic defaults).
3. Compile canonical location IDs and registry updates deterministically from labels.
4. Apply deterministic derivation-only inheritance if eligible.
5. Run full canonical schema validation (including LOC_* and registry membership).
6. If invalid, execute bounded retry policy.

Forbidden behavior:
1. Injecting semantic defaults like `current_location`, `direct_continuation`, or `free` before first validation.
2. Treating non-empty placeholders as valid values.

### 2) Deterministic Derivation-Only Autofill
Allowed derivation only when all conditions hold:
1. Scene handoff is `direct_continuation`.
2. Previous scene has valid `location_end_id`.
3. Previous scene passed validation.
4. Previous scene `location_end_id` is not placeholder/missing.
5. Current scene missing `location_start_id`.

Action:
1. Set `location_start_id = previous.location_end_id`.
2. Record derivation in phase report.

Forbidden derivation:
1. Deriving `location_end_id`.
2. Derivation when `handoff_mode != direct_continuation`.
3. Derivation from invalid or unvalidated previous scene state.

If conditions fail:
1. Do not fill.
2. Emit validation error.

### 3) Location Registry Artifact
Introduce a run-scoped outline location registry artifact:
1. Canonical path: `outline/pipeline_runs/<run_id>/outline_location_registry_v1.json`
2. Includes `locations[]` entries with `location_id`, `display_name`, `aliases`, `introduced_in`, optional `parent_location_id`, and `stability_key`.
3. Includes `location_registry_delta[]` in phase outputs when new locations are introduced.

Validation:
1. Every `location_start_id` and `location_end_id` must exist in final registry state for that phase.
2. Registry references must be unique and deterministic.

Published active registry requirement:
1. On successful outline completion, promote run registry to:
   - `outline/location_registry_active.json`
2. Record promoted registry hash and source run id in:
   - `outline_pipeline_report.json`
   - final outline metadata block.
3. Scene-card/planner consumers must read active published registry, not "latest run folder" by discovery.

### 4) Deterministic LOC_* ID Generation
Model provides location labels; orchestrator owns canonical ID generation.

Policy:
1. Canonical generation input is normalized display name plus optional parent location context.
2. Generate `LOC_<NORMALIZED_SLUG>`.
3. If collision, append deterministic suffix derived from stable hash of canonical generation input.
4. Persist mapping in registry and reuse in later phases and retries.
5. Alias policy:
   - If a new emitted location label resolves to an existing canonical location under deterministic alias rules, reuse existing `location_id`.
   - Store new label in `aliases[]`.
   - Do not mint a new ID when alias resolution succeeds.

### 5) Retry Contract (Bounded)
1. Max attempts per phase remains 2.
2. One retry only for fixable schema/placeholder/registry misses.
3. Retry prompt context includes compact grouped fix list, failed field paths, and relevant prior scene/registry context.
4. If second attempt fails with the same top-level reason code and same first offending pattern/span, short-circuit to terminal `ERROR` with `requires_user_attention=true`.
5. If second attempt fails for any other reason, terminate per matrix (`ERROR` or `PAUSED`) with full report output.
6. Retry input must include prior attempt parse/validation diagnostics, not only first error.

### 5a) `error_v1` Schema and Routing
`error_v1` must be schema-validated as a first-class response shape.

Required keys:
1. `result` (`ERROR`)
2. `schema_version` (`error_v1`)
3. `error_type`
4. `reason_code`
5. `missing_fields[]`
6. `phase`
7. `action_hint`
8. `validator_evidence[]` (when applicable)

Routing:
1. `error_v1` reason codes in retryable class trigger bounded retry.
2. Non-retryable `error_v1` reason codes terminate immediately with `ERROR`.
3. All `error_v1` terminal events must set reason codes in report + console summary.

### 6) Visibility + Write Gate
Every outline run must emit:
1. Console summary (success and failure).
2. `outline_pipeline_report.json` (success and failure).

Required report keys:
1. `overall_status`
2. `requires_user_attention`
3. `attention_items[]`
4. `phase_failed`
5. `top_errors[]`
6. `location_identity_summary`
7. `seam_summary`
8. `attempt_usage`
9. `reason_codes`
10. `template_checksums`
11. `raw_model_output_path` when parse fails
12. `retry_directive` when retryable failure occurs

Write gate:
1. `bookforge run` must refuse when latest outline `overall_status` is not `SUCCESS` or `SUCCESS_WITH_WARNINGS`.
2. `bookforge run` must also refuse when `requires_user_attention=true`, unless override policy permits.
3. Continue only with explicit `--ack-outline-issues` for `SUCCESS_WITH_WARNINGS` attention cases.
4. Gate message must print a hard banner:
   - `WRITE GATED: outline status=<terminal_status>. See <report_path>.`
   - `Use --ack-outline-issues only for SUCCESS_WITH_WARNINGS attention cases.`

Parse failure reporting requirement:
1. Even when phase output cannot be parsed as JSON, write `outline_pipeline_report.json`.
2. Include parse error details and reference to raw model output artifact.
3. Write stable latest-report pointer:
   - `outline/outline_pipeline_report_latest.json` (copy or pointer metadata).

### 7) Canonical Transition Field Naming and Alias Normalization
Canonical transition fields:
1. `transition_in_text`
2. `transition_in_anchors`
3. `transition_out_text`
4. `transition_out_anchors`

Compatibility rule:
1. Legacy alias `transition_in` may be accepted only by explicit normalization step.
2. Legacy alias `transition_out` may be accepted only by explicit normalization step.
3. Alias normalization executes before schema validation.
4. Post-normalization payload must not retain both canonical and alias variants.

### 8) Template Drift Guard
At outline run start:
1. Compare book-local outline template checksums against active compiled checksums.
2. If drift detected, fail fast with actionable message:
   - `Run: bookforge book update-templates --book <book_id>`

## Concrete Implementation Checklist (File-by-File)

### Code
- [ ] `src/bookforge/outline.py`
  - Add raw-first validation order (no semantic prefill before first validation).
  - Validate label-level location fields before ID compilation.
  - Compile canonical location IDs from labels deterministically (orchestrator-owned).
  - Restrict autofill to derivation-only inheritance rule.
  - Add placeholder rejection across transition/location fields.
  - Add location registry load/update/validate path.
  - Add active registry publish step and metadata/hash recording.
  - Add deterministic LOC_* ID generation helper.
  - Add alias resolution helper to reduce registry churn across retries.
  - Add grouped retry fix-list payload generation.
  - Add same-failure short-circuit on attempt 2 when reason code + offending span pattern repeats.
  - Always write `outline_pipeline_report.json` on failure and success.
  - Emit report on parse failures with raw output path and retry directive.
  - Maintain stable latest-report pointer `outline/outline_pipeline_report_latest.json`.
  - Include location identity and derivation events in phase/report metrics.
  - Add template checksum drift guard at run start.
- [ ] `src/bookforge/phases/plan.py`
  - Ensure scene-card payload propagates `location_start_id`, `location_end_id`, transition fields, and registry references verbatim.
  - Ensure canonical transition-out fields (`transition_out_text`, `transition_out_anchors`) are propagated.
  - Ensure no fallback defaults for handoff/constraint enums.
- [ ] `src/bookforge/runner.py`
  - Enforce hard gate on outline terminal status before writing (`PAUSED` and `ERROR` always block).
  - Enforce attention gate for `SUCCESS_WITH_WARNINGS` with override policy.
  - Print condensed outline attention summary on gate failure.
- [ ] `src/bookforge/cli.py`
  - Add or confirm `--ack-outline-issues` behavior and help text.
  - Surface template-drift and outline-attention errors clearly with required status/phase/reason summary fields.
- [ ] `src/bookforge/workspace.py`
  - Add helper for checking compiled-to-book template checksum consistency (or route through outline module helper).
- [ ] `src/bookforge/pipeline/outline.py`
  - Use `outline/location_registry_active.json` as canonical runtime registry source for scene-card/planning context.

### Schemas
- [ ] `schemas/outline.schema.json`
  - Add `location_registry` (or registry reference contract) for outline phases where applicable.
  - Add required label-level location fields for model output contract (`location_start_label`, `location_end_label`) where phase outputs are validated pre-compilation.
  - Add strict key requirements for chapter/section/scene completeness already enforced in phase 03+.
  - Add placeholder-ban constraints where schema-expressible.
  - Align transition-out canonical field names (`transition_out_text`, `transition_out_anchors`).
- [ ] `schemas/scene_card.schema.json`
  - Keep required transition/location identity fields.
  - Align transition-out canonical field names.
  - Ensure no nullable fallback paths for required transition fields.
- [ ] `schemas/error_v1.schema.json` (new)
  - Define `error_v1` keys and validation contract.
  - Integrate via `oneOf` routing in outline phase validation path.
- [ ] `schemas/outline_pipeline_report.schema.json` (new)
  - Define required failure/success summary keys including parse-failure payload fields.
- [ ] `schemas/outline_location_registry.schema.json` (new)
  - Define canonical registry shape and delta shape.
- [ ] `schemas/outline_error_codes.schema.json` (new or folded into report schema)
  - Define reason-code taxonomy for retryable/non-retryable/pause conditions.

### Prompt Blocks (Source of Truth)
- [ ] `resources/prompt_blocks/phase/outline_pipeline/outline_system_execution_mode_strict.md` (new)
  - Add the outline-specific system instruction block from this plan.
- [ ] `resources/prompt_blocks/phase/outline_pipeline/phase_01_chapter_spine_prompt_contract.md`
  - Include outline system block and strict JSON/`error_v1` behavior references.
- [ ] `resources/prompt_blocks/phase/outline_pipeline/phase_02_section_architecture_prompt_contract.md`
  - Include registry introduction guidance, strict JSON/`error_v1` behavior, and section closure persistence.
- [ ] `resources/prompt_blocks/phase/outline_pipeline/phase_03_scene_draft_prompt_contract.md`
  - Enforce full required chapter/section/scene key completeness.
  - Enforce required label-level location naming and registry delta requirements.
  - Enforce no placeholder/no synthetic anchor policy.
  - Keep canonical transition names only (`transition_in_text`, `transition_in_anchors`, `transition_out_text`, `transition_out_anchors`).
- [ ] `resources/prompt_blocks/phase/outline_pipeline/phase_04_transition_causality_refinement_prompt_contract.md`
  - Preserve and improve existing IDs; require reason on field degradation.
  - Keep canonical transition names only and strict JSON/`error_v1` behavior.
- [ ] `resources/prompt_blocks/phase/outline_pipeline/phase_05_cast_function_refinement_prompt_contract.md`
  - Preserve transition/location identity fields and registry references.
  - Keep canonical transition names only and strict JSON/`error_v1` behavior.
- [ ] `resources/prompt_blocks/phase/outline_pipeline/phase_06_thread_payoff_refinement_prompt_contract.md`
  - Preserve transition/location identity fields and registry references.
  - Keep canonical transition names only and strict JSON/`error_v1` behavior.

### Prompt Composition Manifests
- [ ] `resources/prompt_composition/manifests/outline_phase_01_chapter_spine.composition.manifest.json`
- [ ] `resources/prompt_composition/manifests/outline_phase_02_section_architecture.composition.manifest.json`
- [ ] `resources/prompt_composition/manifests/outline_phase_03_scene_draft.composition.manifest.json`
- [ ] `resources/prompt_composition/manifests/outline_phase_04_transition_causality_refinement.composition.manifest.json`
- [ ] `resources/prompt_composition/manifests/outline_phase_05_cast_function_refinement.composition.manifest.json`
- [ ] `resources/prompt_composition/manifests/outline_phase_06_thread_payoff_refinement.composition.manifest.json`
  - Insert new outline system execution block in each outline phase template composition.

### Compiled Templates and Checksums
- [ ] `resources/prompt_templates/outline_phase_01_chapter_spine.md`
- [ ] `resources/prompt_templates/outline_phase_02_section_architecture.md`
- [ ] `resources/prompt_templates/outline_phase_03_scene_draft.md`
- [ ] `resources/prompt_templates/outline_phase_04_transition_causality_refinement.md`
- [ ] `resources/prompt_templates/outline_phase_05_cast_function_refinement.md`
- [ ] `resources/prompt_templates/outline_phase_06_thread_payoff_refinement.md`
- [ ] `resources/prompt_composition/source_of_truth_checksums.json`
- [ ] `resources/prompt_composition/reports/compiled_trace/*.trace.json` (affected outline phase templates)
- [ ] `resources/prompt_composition/reports/compiled_debug/*.md` (affected outline phase templates)

### Docs
- [ ] `docs/help/outline_generate.md`
  - Document strict JSON execution mode and location registry behavior.
  - Document placeholder rejection and retry/pause outcomes.
  - Document template-drift failure and remediation command.
  - Document terminal status taxonomy and console summary fields.
  - Document orchestrator-owned location ID compilation (labels in model output, IDs in canonical artifacts).
- [ ] `docs/help/run.md`
  - Document write hard-gate on outline attention.
  - Document write hard-gate on non-success terminal statuses.
  - Document `--ack-outline-issues` semantics.
  - Document hard write-gate banner semantics.
- [ ] `docs/help/book.md` or command-specific help file if present
  - Document `book update-templates` as required sync step when drift detected.

### Tests
- [ ] `tests/test_outline_generate.py`
  - Add failure test for placeholder location values.
  - Add label-to-ID deterministic compilation test.
  - Add derivation-only inheritance test.
  - Add write-gate status policy test fixture setup (`PAUSED`/`ERROR` always block).
  - Add template-drift guard failure test.
  - Add failed-run `outline_pipeline_report.json` emission test.
- [ ] `tests/test_outline_transition_policy.py`
  - Add no-semantic-autofill assertion.
  - Add registry membership enforcement for all scene location IDs.
  - Add strict derivation-only rules: derive start only on direct continuation from validated prior scene.
  - Add non-derivation assertions for non-direct handoffs.
  - Add retry fix-list evidence behavior test.
- [ ] `tests/test_plan_scene.py`
  - Ensure scene-card propagation keeps location IDs and transition fields unchanged.
- [ ] `tests/test_prompt_composition.py`
  - Verify new outline system block is included in all six outline phase compiled templates.
- [ ] `tests/test_run.py` or equivalent runner test file
  - Add write hard-gate tests for terminal statuses and attention override behavior.
- [ ] `tests/test_outline_reports.py` (new)
  - Validate success/failure report schema and required keys.
  - Validate parse-failure report emission and required parse diagnostics fields.
  - Validate latest-report pointer artifact behavior.
- [ ] `tests/test_outline_location_registry.py` (new)
  - Validate deterministic LOC ID generation, collision behavior, alias reuse, and active-registry publish semantics.
  - Validate optional `parent_location_id` and `stability_key` persistence.

## Delivery Sequence
1. Implement core validator/order/autofill restrictions in `src/bookforge/outline.py`.
2. Add location registry artifact and deterministic ID generation.
3. Add failure visibility/report schema and runner hard-gate.
4. Add outline-specific system instruction block and wire manifests.
5. Recompose templates and update checksums.
6. Update docs/help.
7. Run targeted tests, then end-to-end rerun audit on `criticulous_b1`.

## Acceptance Criteria
1. Outline phase 03 can no longer pass with placeholder location identity or masked semantic defaults.
2. All scene location IDs in phase outputs are registry-resolved and deterministic.
3. Failed outline runs always produce `outline_pipeline_report.json` and pause marker with actionable errors.
4. `bookforge run` blocks whenever outline terminal status is `PAUSED` or `ERROR` regardless of acknowledgement flags.
5. `bookforge run` blocks on outline attention unless explicit acknowledgement override is provided for allowed warning states.
6. End-to-end rerun for `criticulous_b1` surfaces failures clearly and does not silently degrade into defaults.

## Open Decisions (Resolve Before Implementation Start)
1. Exact deterministic alias matching policy thresholds for location label reuse.
2. Final LOC ID collision suffix format.
3. Whether `--pause-on-attention` is enabled in this implementation slice or deferred.
