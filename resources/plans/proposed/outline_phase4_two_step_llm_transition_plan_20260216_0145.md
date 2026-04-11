# Phase 04 Two-Step LLM Transition Plan (20260216_0145)

## Purpose
Define an explicit, enforceable two-step implementation for phase 04 so seam detection and seam execution both remain LLM-authored at the semantic layer.

This plan addresses the prior failure class:
1. LLM identified seams.
2. Code inserted scenes/fallback transition text.
3. Placeholder semantics survived into accepted artifacts.

## Doctrine Anchor
This plan is governed by:
1. `resources/plans/proposed/outline_pipeline_doctrine_manifesto_20260216_0205.md`

Locked doctrine statement:
1. LLM authors and lints; orchestrator never authors or discards; orchestrator only enforces validated state and deterministic invariants.

## Outcome Requirement
If a seam requires a transition scene:
1. The scene must be authored by LLM in phase 04B.
2. If LLM does not author it, phase 04 fails.
3. Deterministic code may not synthesize replacement semantic content.

## Long-Term Execution Direction
1. All outline phases will migrate to a two-turn model (`T1` plan -> `T2` execute) when stable.
2. All outline phases will prefer chapter-by-chapter execution where possible (scene-by-scene where already used).
3. Phase 04A/04B are the first enforced chapter-scoped two-turn steps in this plan.

## Phase 04 Decomposition
Prompt contract sources:
1. 04A source (existing): `resources/prompt_blocks/phase/outline_pipeline/phase_04_transition_causality_refinement_prompt_contract.md`
2. 04B source (new): `resources/prompt_blocks/phase/outline_pipeline/phase_04b_transition_execution_prompt_contract.md`

Composed templates:
1. `resources/prompt_templates/outline_phase_04a_transition_seam_analysis.md`
2. `resources/prompt_templates/outline_phase_04b_transition_execution.md`

### 04A: Seam Analysis LLM Step (Chapter-Scoped)
Objective:
1. analyze adjacent scene edges,
2. produce seam scores/resolution recommendations,
3. return candidate edges that require insertion.

Input payload:
1. target chapter outline slice only (no full-book payload),
2. compact neighbor context (optional, read-only),
3. transition hints filtered to chapter,
4. policy settings:
   - strict transition mode,
   - insertion budget,
   - scene-count mode.

Output payload:
1. chapter-only seam analysis artifact,
2. `phase_report` with:
   - `candidate_seams[]` entries:
     - `from_scene_ref`
     - `to_scene_ref`
     - `seam_score`
     - `requested_resolution` (`inline_bridge|micro_scene|full_scene`)
     - `reason`.

Validation gates:
1. schema and required phase fields,
2. candidate ref format and existence checks,
3. seam score numeric range checks.

### 04B: Seam Execution LLM Step (Chapter-Scoped)
Objective:
1. resolve selected seam candidates,
2. author inserted transition scenes for selected `micro_scene`/`full_scene` candidates,
3. return a coherent outline with valid sequencing and links.

Input payload:
1. 04A validated output for the target chapter only,
2. deterministic routing block:
   - `selected_candidates[]`,
   - `blocked_candidates[]` with reasons,
   - `downgrade_constraints[]`,
   - exact-mode conflict markers if relevant.
3. 04A-to-04B handoff block scoped to chapter (`outline_phase_04a_output_chapter`).

Output payload:
1. chapter-only outline patch,
2. `phase_report` with:
   - `inserted_scene_refs[]`,
   - `blocked_by_budget[]`,
   - `downgraded_resolution[]`,
   - `unresolved_required_insertions[]`,
   - `edits_applied[]`.
3. Scene additions fully authored by LLM for each selected insertion candidate.

Validation gates:
1. all selected insertion candidates are resolved by authored scene insertion or explicit terminal error,
2. inserted scene objects contain full required scene contract fields,
3. no placeholder or meta fallback phrasing in transition fields,
4. links and scene ordering remain valid.

## Deterministic Routing Logic (Non-Semantic)
Routing is deterministic, authoring is not.

Allowed routing logic:
1. enforce insertion budget,
2. enforce exact-count policy,
3. deterministic tie-break:
   - highest score,
   - earliest source scene index,
   - lexical ref tie-break.

Required routing visibility:
1. each non-selected insertion candidate must be listed with reason code.
2. no candidate may disappear without explanation.

Forbidden routing behavior:
1. semantic scene insertion by code,
2. semantic transition text fallback by code,
3. unlogged silent downgrades.

## Retry Contract
04A and 04B each support bounded retries.

Default:
1. max attempts per step: 2.

04A retryable:
1. strict JSON parse fail,
2. schema fail,
3. candidate ref/type fail.

04B retryable:
1. selected insertion unresolved,
2. invalid inserted scene contract,
3. placeholder/meta transition field failures,
4. link/ordering regressions introduced during insertion.

Critical retry cap:
1. unresolved required insertion failures may use a separate critical retry cap (default 2 additional attempts) if enabled.
2. on exhaustion: terminal `ERROR`.

## Error Contracts
`error_v1` reason codes for this phase:
1. `phase04a_candidate_contract_invalid`
2. `phase04b_required_insertion_unresolved`
3. `phase04b_inserted_scene_contract_invalid`
4. `phase04_exact_scene_count_transition_conflict`
5. `phase04_transition_semantics_invalid`

## Prompt Contract Requirements
### 04A prompt must
1. request candidate seam extraction and resolution recommendations,
2. require explicit candidate list with refs/scores/reasons,
3. forbid commentary outside JSON.
4. output a stable candidate list for deterministic routing (no hidden candidate derivation in code).

### 04B prompt must
1. include selected candidate list from routing layer,
2. explicitly instruct LLM to author inserted scenes for each selected candidate,
3. prohibit leaving selected candidates unresolved,
4. include strict invalid-output fallback: return `error_v1` if constraints cannot be met.
5. explicitly state: "Do not leave selected insertion candidates unresolved."
6. explicitly state: "All inserted scene semantic fields must be authored prose, not meta placeholders."

## Compiler/Manifest Touchpoints (Explicit)
Required files to add/update:
1. `resources/prompt_blocks/phase/outline_pipeline/phase_04b_transition_execution_prompt_contract.md` (new)
2. `resources/prompt_templates/outline_phase_04a_transition_seam_analysis.md` (new or split output)
3. `resources/prompt_templates/outline_phase_04b_transition_execution.md` (new)
4. `resources/prompt_composition/manifests/outline_phase_04a_transition_seam_analysis.composition.manifest.json` (new)
5. `resources/prompt_composition/manifests/outline_phase_04b_transition_execution.composition.manifest.json` (new)
6. `resources/prompt_composition/prompt_tokens_allowlist.json` (add phase-04 step placeholders)
7. `resources/prompt_composition/source_of_truth_checksums.json` (refresh)
8. `src/bookforge/workspace.py` (`PROMPT_TEMPLATE_FILES` update)

## 04B Placeholder Contract (Proposed Lock)
To avoid runtime/render drift, 04B should use explicit JSON blob placeholders:
1. `{{outline_phase_04a_output}}`
2. `{{phase_04_selected_candidates_json}}`
3. `{{phase_04_blocked_candidates_json}}`
4. `{{phase_04_policy_context_json}}`

Renderer requirements:
1. Values are injected as raw JSON text blocks in prompt context.
2. Missing placeholder data is a hard render failure for 04B.
3. 04B execution must not continue with missing routing payload.

## Runtime Wiring Touchpoints (Explicit)
1. `src/bookforge/outline.py` remains orchestration shell and dispatches to phase modules.
2. `src/bookforge/phases/outline/phase_04a_transition_seam_analysis.py` handles 04A render/execute/validate flow.
3. `src/bookforge/phases/outline/phase_04b_transition_execution.py` handles 04B render/execute/validate flow.
4. 04B render context must include selected/blocked/policy JSON payload blocks.
5. Routing payload artifacts must be persisted before rendering 04B.
6. 04B validation must assert selected insertions were resolved by LLM output, not post-hoc code mutation.
7. 04B retry directives must include failing selected candidate refs and unresolved insertion reasons.

## Field Semantics for Inserted Scenes
Inserted scene minimum required fields:
1. `scene_id`
2. `summary`
3. `type`
4. `outcome`
5. `characters`
6. `location_start`, `location_end`
7. `location_start_label`, `location_end_label`
8. `handoff_mode`
9. `constraint_state`
10. `transition_in_text`, `transition_in_anchors`
11. `transition_out_text`, `transition_out_anchors` (if non-last)
12. `consumes_outcome_from`, `hands_off_to` as applicable
13. `seam_score`, `seam_resolution`
14. `inserted_by_pipeline` (true)
15. `insert_reason`

## Anti-Placeholder and Anti-Meta Rules
Transition semantic fields fail if containing:
1. placeholder identity tokens (`current_location`, `unknown`, `tbd`, `placeholder`, `here`, `there`),
2. meta fallback phrasing (`this beat`, `realized on page`, `movement from X to Y`),
3. ID-token-only anchors (`LOC_*`, enum values only, or token soup without prose-level semantic anchors).

Failure handling:
1. route to LLM correction in 04B retry,
2. do not auto-repair deterministically.

## Exact Scene Count Policy
1. In exact mode, insertion-required candidates produce conflict error unless explicit future policy allows compensating merge/removal.
2. 04B must not silently convert selected insertions to inline bridge to satisfy exact count.
3. conflict must be surfaced in report and console summary.

## Artifacts for Auditability
Required artifacts:
1. `phase_04a_input.json`
2. `phase_04a_attempt_N.raw.json`
3. `phase_04a_output.json`
4. `phase_04a_validation.json`
5. `phase_04b_input.json`
6. `phase_04b_attempt_N.raw.json`
7. `phase_04b_output.json`
8. `phase_04b_validation.json`
9. `phase_04_transition_decision_trace.json`

Decision trace minimum fields:
1. all candidates,
2. selected candidates,
3. blocked candidates,
4. downgrades and reasons,
5. unresolved required insertions,
6. terminal phase status.

## Test Matrix
1. 04A emits insertion candidates; 04B authors inserted scenes; pass.
2. 04A emits candidates; 04B omits selected insertion; retry then fail.
3. 04B inserted scenes include placeholder/meta transition text; retry then fail.
4. exact-count mode with required insertion emits conflict error.
5. blocked-by-budget candidates are visible in trace/report.
6. no deterministic semantic insertion occurs in code path.
