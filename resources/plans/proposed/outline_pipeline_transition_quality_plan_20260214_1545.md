# Outline Pipeline Transition Quality Plan (20260214_1545)

## Purpose
Create a focused v2.1 refinement plan that preserves the approved baseline in `resources/plans/proposed/outline_pipeline_refinement_plan_20260214_0615.md` while adding hard, end-to-end transition quality controls that eliminate teleport-like scene seams.

This plan is an additive refinement, not a replacement. Baseline decisions remain active unless explicitly superseded here.

## Baseline Preservation (No Regression)
The following baseline locks remain unchanged and are not reopened:
1. One-pass outline generation is removed from active production flow.
2. Compiler/composition remains the only prompt source-of-truth path.
3. Existing six-phase outline orchestration remains in place.
4. Existing rerun and resume behavior remains in place, including dependency and fingerprint checks.
5. Existing sequencing and registry integrity gates remain in place.
6. Existing section closure policy (`end_condition` and `end_condition_echo`) remains in place.

## Adopted Reviewer Delta Locks (2026-02-14)
The following refinements are adopted as hard requirements for v2.1:
1. Phase-03 transition fields are hard-required. Missing/empty values fail the phase immediately; downstream phases cannot "fill later."
2. Exact scene-count interaction with insertion is explicitly controlled:
   - non-exact modes allow insertion subject to budget and validator policy,
   - exact-count mode disables transition-scene insertion by default,
   - if a seam requires insertion under exact mode, phase fails with explicit conflict reason.
3. Insertion budget selection uses deterministic tie-breaks when multiple seams qualify.
4. Custody/authority seam scoring must use explicit machine fields (`constraint_state`) rather than free-text inference.
5. Strict mode constrains `hard_cut` usage and requires explicit justification metadata.
6. Transition realization hardening uses `transition_in_text` + `transition_in_anchors` for deterministic write/lint checks.
7. User-visible surfacing and run-report visibility are mandatory; downgrade/skip/fail states cannot be artifact-only.
8. Retry/stop behavior is explicit and deterministic; auto-retry is bounded and reason-scoped.

## Problem Statement
Current improvements solve graph-level continuity better than before, but they do not reliably force rendered transition handoffs in prose.

Observed failure mode:
1. Outline graph integrity can pass (`consumes_outcome_from` and `hands_off_to`) while prose still hard-cuts location/state.
2. Transition intent may be present in planning context but not elevated to strict write-time obligations.
3. Lint currently lacks a dedicated seam detector for missing transition realization.

Result:
- Graph passes, prose can still teleport.

## Primary Objective (v2.1)
Make scene transition quality a hard gate by enforcing:
1. Required transition payload in outline phases.
2. Guaranteed propagation of transition payload into scene cards.
3. Write-time realization requirements for non-direct handoffs.
4. Lint-time seam detection and repair routing.
5. Optional deterministic insertion of transition scenes when seams are too high-risk for inline bridging.

## Scope
In scope:
1. Transition contract hardening from outline phase 03 onward.
2. Deterministic seam scoring and seam resolution (`inline_bridge`, `micro_scene`, `full_scene`).
3. Transition scene insertion policy and safeguards.
4. Scene-card schema and planner propagation updates.
5. Write and lint contract/gate updates.
6. Validation/test/reporting updates.

Out of scope:
1. Reworking full story architecture beyond transition quality.
2. Non-transition prose-style optimization as a primary objective.
3. Broad phase-count changes (six-phase outline pipeline remains).

## Transition Contract v2.1 (Required)
Starting at phase 03, transition data is mandatory, not optional.

### Required transition fields on scene objects
For every non-first scene in chapter:
1. `location_start` (string, non-empty)
2. `location_end` (string, non-empty)
3. `handoff_mode` (enum, non-empty)
4. `constraint_state` (enum, non-empty)
5. `transition_in_text` (string, non-empty)
6. `transition_in_anchors` (array of 3-6 non-empty strings)
7. `consumes_outcome_from` (`chapter_id:scene_id`)

For every non-last scene in chapter:
1. `transition_out` (string, non-empty)
2. `hands_off_to` (`chapter_id:scene_id`)

For chapter-first scenes:
1. `location_start`, `location_end`, `handoff_mode`, `constraint_state`, `transition_in_text`, and `transition_in_anchors` remain required.
2. `consumes_outcome_from` is omitted.

For chapter-last scenes:
1. `transition_out` may be omitted.
2. `hands_off_to` is omitted.

Phase-03 failure policy:
1. Missing required transition fields are hard errors.
2. Empty strings are hard errors.
3. Placeholder/null marker strings are hard errors.
4. A failed transition contract in phase 03 blocks progression to phase 04.
5. Phase 03 validators may not auto-fill, auto-repair, or downgrade missing required transition fields.

### Handoff mode enum (initial)
1. `direct_continuation`
2. `escorted_transfer`
3. `detained_then_release`
4. `time_skip`
5. `hard_cut`
6. `montage`
7. `offscreen_processing`
8. `combat_disengage`
9. `arrival_checkpoint`
10. `aftermath_relocation`

Strict-mode `hard_cut` policy:
1. `hard_cut` is disallowed by default in strict mode.
2. Exception requires all of:
   - `hard_cut_justification` (non-empty string),
   - `intentional_cinematic_cut` (boolean true),
   - `transition_in_text` and anchors still present,
   - inline bridge marker still required in opening span.

### Constraint state enum (initial)
1. `free`
2. `pursued`
3. `detained`
4. `processed`
5. `sheltered`
6. `restricted`
7. `engaged_combat`
8. `fleeing`

### Transition text rules
1. `transition_in_text` must describe connective action, not section summary.
2. `transition_out` must describe the push condition into the next scene.
3. Empty strings are invalid; unknown values must be resolved in-phase or fail.
4. `transition_in_text` must be bridge-action oriented and not recap exposition.
5. `transition_in_anchors` must contain concrete, checkable transition terms used by lint.
6. Legacy `transition_in` field is allowed only as input-compat alias and is normalized to `transition_in_text` before validation.
7. Optional transition fields must be omitted when inapplicable, never emitted as empty strings.

## Seam Triage Model (Deterministic)
Add deterministic edge scoring to decide whether to bridge inline or insert a scene.

### New seam fields (edge/downstream-scene level)
1. `seam_score` (integer 0-100)
2. `seam_resolution` (enum)
   - `inline_bridge`
   - `micro_scene`
   - `full_scene`

### Deterministic seam score heuristics (initial)
1. Location delta: +25 when named location changes.
2. Custody/authority delta: +35 when `constraint_state` shifts between constrained and free classes.
3. Time delta: +15 when not continuous or unknown.
4. Cast/faction delta: +10 when new recurring actor/faction enters via seam.
5. Rule/procedure delta: +10 when procedural world rules are implied in gap.
6. Intensity mismatch: +10 when high-pressure to low-pressure in adjacent scenes.
7. Post-turn seam: +10 after major event turns (scan anomaly, bounty, curse broadcast, etc.).

Scoring input source lock:
1. Seam scorer must use explicit structured fields (`location_*`, `constraint_state`, `time_delta`, cast/thread deltas, etc.).
2. Free-text-only inference is prohibited for deterministic seam scoring.

### Resolution thresholds
1. 0-24: `inline_bridge`
2. 25-54: `micro_scene`
3. 55+: `full_scene`

## Transition Scene Insertion Policy
Phase 04 is authorized to insert scene nodes when seam resolution requires it.

### Insertion behavior
Transform:
- Scene A -> Scene B

Into:
- Scene A -> Inserted Scene X -> Scene B

### Inserted scene metadata
Required:
1. `inserted_by_pipeline` (boolean true)
2. `insert_reason` (string)
3. `insert_origin_edge` (`chapter:scene` -> `chapter:scene`)
4. `seam_score` (integer)
5. `seam_resolution` (`micro_scene` or `full_scene`)

### Inserted scene target lengths (planning targets)
1. `micro_scene`: 300-900 words
2. `full_scene`: 1200-2500 words

### Value-hook requirement for inserted scenes
An inserted scene must satisfy at least one:
1. Introduces a reusable world rule/procedure.
2. Introduces a reusable incidental NPC/faction touchpoint.
3. Produces a durable consequence carried forward.
4. Produces a character intent shift.
5. Sets a concrete payoff hook.

If none apply, resolver must downgrade to `inline_bridge`.

### Insertion budget safeguard
Default:
1. Max 1 inserted transition scene per chapter.

Configurable:
1. strict mode can increase budget.
2. budget and inserts must be logged in phase report and run report.

### Exact count interaction lock
1. In non-exact modes, insertion is allowed subject to seam resolution thresholds and chapter insertion budget.
2. In exact scene-count mode, transition-scene insertion is disabled by default.
3. If seam resolution requires `micro_scene` or `full_scene` while exact mode is active:
   - phase fails with reason code `exact_scene_count_transition_conflict`,
   - no silent downgrade to `inline_bridge` is allowed.
4. A future compensating merge/removal strategy is out-of-scope for v2.1 unless explicitly approved.

### Deterministic insertion selection (budget conflicts)
When multiple seams exceed insertion threshold and budget is limited:
1. select highest `seam_score`,
2. tie-break by earliest chapter-local source scene index,
3. final tie-break by lexical order of edge ref (`from->to`).

Required reporting:
1. selected seam(s),
2. non-selected seam candidates blocked by budget,
3. deterministic tie-break reason.

## Propagation Contract (No Signal Drop)
Transition payload must survive from outline to scene card to write/lint.

### Outline -> planner (`outline_window`)
Planner input must include:
1. all required transition fields
2. seam fields (`seam_score`, `seam_resolution`)
3. insertion metadata when applicable

### Planner -> scene card
Scene card must carry transition fields verbatim:
1. `location_start`
2. `location_end`
3. `handoff_mode`
4. `constraint_state`
5. `transition_in_text`
6. `transition_in_anchors`
7. `transition_out`
8. `consumes_outcome_from`
9. `hands_off_to`
10. `seam_resolution`
11. `seam_score`

No re-derivation by writer.

## Write-Phase Enforcement
Maintain "start in motion" while requiring connective realization.

### Required behavior
If `handoff_mode != direct_continuation`:
1. opening paragraph must realize `transition_in_text` in 1-3 sentences
2. no recap block dumping
3. continue immediately into scene action
4. connective realization must contain:
   - at least one concrete action verb, and
   - at least one concrete world noun tied to the handoff context.

Realization matching policy:
1. hardening mode accepts either:
   - verbatim `transition_in_text`, or
   - equivalent phrasing containing all `transition_in_anchors` in the opening span.
2. missing both is a transition compliance failure.

If `seam_resolution` is:
1. `inline_bridge`: required opening bridge sentences
2. `micro_scene` or `full_scene`: inserted scene must realize transition goal and end in required handoff state

### Optional debugging scaffold during hardening
Allow temporary compliance line:
- `TRANSITION_CHECK: <from> -> <to> via <handoff_mode>`

Can be removed once seam regressions stabilize.

## Lint-Phase Enhancement
Add seam-specific issue code:
1. `transition_bridge_missing`

### Trigger conditions
1. prior/next scene location or handoff metadata implies discontinuity, and
2. opening span (first paragraph or first 400 characters, whichever is shorter) lacks required transition realization evidence (`transition_in_text` or all anchors)

### Evidence policy
1. include offending opening line excerpt
2. include expected handoff mode and transition_in summary

### Severity policy
1. warning in non-strict mode during ramp
2. error in strict transition mode

## Section Closure Persistence (No Field Loss)
Preserve section-level `end_condition` across phase 03, 04, 05, 06 outputs.

Current anti-pattern to eliminate:
- phase 02 contains section `end_condition`, later phases retain only `end_condition_echo`.

Required:
1. section-level `end_condition` remains present through final outline
2. `end_condition_echo` still required on section-final scene
3. validator fails if section end_condition is dropped downstream

## Schema and Contract Changes
### `schemas/outline.schema.json`
Add explicit scene properties (kept as additional properties currently, but now required by validator):
1. `location_start`, `location_end`, `handoff_mode`
2. `constraint_state`
3. `transition_in_text`, `transition_in_anchors`, `transition_out`
4. `consumes_outcome_from`, `hands_off_to`
5. `seam_score`, `seam_resolution`
6. insertion metadata fields
7. strict-mode hard-cut metadata fields (`hard_cut_justification`, `intentional_cinematic_cut`)

### `schemas/scene_card.schema.json`
Add required properties:
1. transition payload fields listed in propagation contract
2. keep existing required scene-card fields

### Shared `error_v1`
No change in shape; ensure transition validation errors map cleanly into reason-coded output.

## Prompt Template/Block Updates (Planned)
### Outline pipeline prompt blocks
1. `resources/prompt_blocks/phase/outline_pipeline/phase_03_scene_draft_prompt_contract.md`
   - transition fields become required
   - seam fields introduced
2. `resources/prompt_blocks/phase/outline_pipeline/phase_04_transition_causality_refinement_prompt_contract.md`
   - seam scoring and resolution required
   - insertion authority and constraints required
3. `resources/prompt_blocks/phase/outline_pipeline/phase_05_cast_function_refinement_prompt_contract.md`
   - preserve transition/seam fields and inserted-scene metadata
4. `resources/prompt_blocks/phase/outline_pipeline/phase_06_thread_payoff_refinement_prompt_contract.md`
   - preserve fields and validate final integrity

### Plan scene-card prompt
1. `resources/prompt_blocks/phase/plan/scene_card_prompt_contract_and_schema.md`
   - transition fields become required in output
   - copy-through requirement from outline_window

### Write and lint prompt blocks/templates
1. `resources/prompt_blocks/phase/write/*` and composed `resources/prompt_templates/write.md`
   - enforce transition realization behavior
2. `resources/prompt_blocks/phase/lint/*` and composed `resources/prompt_templates/lint.md`
   - add `transition_bridge_missing` detector guidance

## Runtime Code Impact Areas
1. `src/bookforge/outline.py`
   - required transition field validation
   - seam scoring + seam resolution
   - insertion logic + renumbering + reference remap
   - section end_condition persistence checks
2. `src/bookforge/phases/plan.py`
   - propagate required transition/seam fields into scene-card generation
3. `src/bookforge/phases/write_phase.py`
   - pass/validate transition payload in write context
4. `src/bookforge/phases/lint_phase.py`
   - deterministic seam detector and issue code
5. `schemas/outline.schema.json`, `schemas/scene_card.schema.json`
   - transition payload structure enforcement
6. `src/bookforge/runner.py` (or run command entrypoint)
   - enforce write gate using latest outline pipeline report
   - print required transition-quality summary before write continuation
7. outline run report serializer
   - write required summary/attention fields for visibility contract

## CLI/Config Additions (Planned)
1. `--transition-insert-budget-per-chapter <int>` (default 1)
2. `--strict-transition-bridges` (promote seam lint to error)
3. `--allow-transition-scene-insertions` (default true)
4. optional `--max-seam-score-inline <int>` override threshold
5. exact-mode insertion behavior lock:
   - default: insertions disabled in exact mode,
   - explicit override flag (future, optional) is not part of v2.1 implementation scope.
6. write gate override flag:
   - `--ack-outline-attention-items` allows `bookforge run` to proceed when outline report requires user attention.
   - default behavior without override is hard stop before writing.

All active mode values must be logged in run metadata.

## User-Visible Surfacing Contract (Hard Requirement)
Outline transition-quality decisions must be visible at run time, not only in artifacts.

### Console summary (always printed)
At the end of `bookforge outline generate`, always print:
1. `Result`: `SUCCESS`, `SUCCESS_WITH_WARNINGS`, `PAUSED`, or `ERROR`.
2. Active mode values:
   - strict transition mode,
   - insertion budget,
   - allow/disable insertion mode,
   - exact scene-count mode.
3. Seam decision counters:
   - inserted scenes count,
   - inline bridges count,
   - hard-cut count,
   - `blocked_by_budget` count.
4. Top-N seam decisions (N=3 default):
   - edge ref (`chapter:scene -> chapter:scene`),
   - seam score,
   - chosen resolution,
   - deterministic reason.
5. If `ERROR`/`PAUSED`/attention state exists, print reason codes and report path.

### Run report contract (always written)
For every run, write `outline_pipeline_report.json` with required summary keys:
1. `overall_status`
2. `warnings_count`
3. `errors_count`
4. `requires_user_attention` (boolean)
5. `attention_items` (array) with reason codes, including at minimum:
   - `blocked_by_budget`
   - `downgraded_resolution`
   - `hard_cut_used`
   - `exact_scene_count_transition_conflict`
6. `mode_values` (strictness/budget/insertion/exact-mode)
7. `top_seam_decisions` (same shape surfaced in console)
8. `artifact_paths` (phase outputs/validation reports)

### Attention severity policy
1. Non-strict mode:
   - `blocked_by_budget` becomes user-attention when any blocked seam score is `>=55`.
2. Strict mode:
   - any blocked seam score `>=55` is an error-level attention item.
   - any insertion-required seam blocked by budget is an error-level attention item.

## Write Gate Contract (No Silent Continuation)
`bookforge run` must read the latest outline pipeline report before writing scene prose.

Required behavior:
1. If `requires_user_attention=false`, proceed normally.
2. If `requires_user_attention=true`:
   - print the same short attention summary and reason codes to console,
   - stop before writing unless `--ack-outline-attention-items` is provided.
3. Override usage (`--ack-outline-attention-items`) must be logged in run metadata and report.

## Retry and Stop Contract (Deterministic)
### Within-phase auto-retry (LLM retry)
1. Max attempts per phase: 2.
2. Auto-retry allowed only when validator emits bounded fix-list errors:
   - missing required fields,
   - schema/type violations,
   - empty/placeholder forbidden values.
3. Auto-retry is not allowed for subjective quality preferences.
4. On second failure, emit `error_v1` and stop.

### Deterministic policy resolution (no LLM retry)
1. Budget conflicts and seam tie-break selection are policy-resolved deterministically without additional LLM attempts.
2. Non-selected seam candidates must be logged with `blocked_by_budget` evidence.
3. Policy-resolved downgrades/conflicts must populate `attention_items`.

### Fail-loud rules
1. Exact mode conflicts must fail with `exact_scene_count_transition_conflict`.
2. Failure summaries must include affected seam refs and reason codes in console + report.

## Resume and Determinism Considerations
1. seam scoring and insertion decisions must be deterministic for unchanged fingerprints.
2. insertion renumbering map must be persisted in phase artifacts for reproducible resume.
3. phase resume invalidation must trigger if transition settings differ from stored run settings.

## Acceptance Tests (Binary)
1. Contract presence:
   - non-first scenes must have required inbound transition fields.
   - non-last scenes must have required outbound transition fields.
   - missing/empty phase-03 transition fields fail immediately and block downstream phases.
2. Propagation:
   - scene card contains transition payload exactly as required.
3. Seam realization:
   - if non-direct handoff, opening span contains either verbatim `transition_in_text` or all anchors.
   - opening span includes at least one action verb and one world noun for bridge realization.
4. Location jump:
   - named location jump without required bridge fails.
5. Custody/authority jump:
   - constrained `constraint_state` -> calm/free without required handoff and bridge fails.
6. Section persistence:
   - section `end_condition` preserved through final outline.
7. Insertion path:
   - seam score above threshold can insert scene and preserve monotonic scene ids + references.
   - tie-break outcome is deterministic and logged when insertion candidates exceed budget.
8. Budget:
   - insertion budget enforced deterministically.
   - non-selected candidates are logged with `blocked_by_budget` evidence.
9. Resume:
   - resume reuses valid phase outputs and respects transition settings fingerprint.
10. Exact mode conflict:
   - exact mode + required insertion returns explicit `exact_scene_count_transition_conflict`.
11. Visibility summary:
   - console summary is always printed and includes mode values + seam counters + top seam decisions.
12. Attention gate:
   - `requires_user_attention=true` blocks `bookforge run` unless `--ack-outline-attention-items` is provided.
13. Retry contract:
   - validator-bounded retry only; max two attempts; no subjective auto-retry.
14. Fail-loud reporting:
   - exact-mode conflicts and budget-blocked high-seam cases are visible in console and `outline_pipeline_report.json`.

## Immediate Pilot Target (Criticulous Chapter 1)
Target seam:
- gate scan/detention -> tavern opening hard cut

Expected v2.1 behavior:
1. seam score exceeds inline threshold.
2. resolver chooses `micro_scene` (or `full_scene` in strict mode).
3. inserted transition scene realizes processing/release handoff.
4. downstream scene starts without teleport seam.
5. if exact mode is enabled for the pilot chapter, the run fails explicitly instead of silently downgrading to inline bridge.

## Implementation Work Packages
### WP1 - Plan/contract hardening
1. Update transition contract text in plan and prompt blocks.
2. Confirm non-regression references to baseline plan.

### WP2 - Validator and schema hardening
1. Add required transition fields and seam validation.
2. Add section end_condition persistence checks.

### WP3 - Seam scoring and insertion engine
1. implement deterministic seam scoring.
2. implement seam resolution.
3. implement insertion + renumber/remap.

### WP4 - Propagation and writer enforcement
1. planner copy-through into scene cards.
2. writer transition realization enforcement.

### WP5 - Lint seam detector
1. add `transition_bridge_missing`.
2. route to repair with focused correction instructions.

### WP6 - Tests and pilot run
1. add unit/integration tests.
2. run chapter 1 scene-by-scene pilot and produce seam delta report.

### WP7 - Visibility, retry, and write-gate controls
1. implement console summary contract for outline runs.
2. implement `outline_pipeline_report.json` summary/attention schema.
3. implement `bookforge run` pre-write attention gate with explicit override flag.
4. add retry-policy tests (bounded fix-list retries only).

## Progress Tracker (v2.1)
Status key: `pending`, `in_progress`, `completed`, `blocked`.

1. v2.1 plan creation: `completed`
2. prompt contract updates: `pending`
3. schema updates: `pending`
4. outline validator updates: `pending`
5. seam scoring/insertion implementation: `pending`
6. planner propagation updates: `pending`
7. write/lint enforcement updates: `pending`
8. test expansion: `pending`
9. chapter 1 pilot validation: `pending`
10. reviewer delta lock integration (phase-03 hard fail, exact-mode interaction, tie-breaks, constraint_state, hard_cut strictness, anchors): `completed`
11. reviewer follow-up clarifications (non-exact insertion allowance, no auto-repair in phase 03, optional field omission rule, explicit opening-span scope): `completed`
12. visibility contract (console + report + attention items): `completed`
13. retry/stop contract and write-gate policy: `completed`

## Review Questions for Next Iteration
1. Should exact-mode insertion remain disabled beyond v2.1, or do we schedule compensating merge/removal strategy in v2.2?
2. Is default insertion budget of 1 per chapter sufficient after chapter-1 and chapter-2 pilots?
3. Should `micro_scene` and `full_scene` length targets remain soft targets, or become hard enforcement in strict mode?
