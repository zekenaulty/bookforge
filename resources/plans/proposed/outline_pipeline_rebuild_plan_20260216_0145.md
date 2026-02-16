# Outline Pipeline Rebuild Plan (20260216_0145)

## Purpose
Rebuild the outline refinement effort from a clean baseline while preserving valid prior work and removing design drift.

This plan supersedes failed experimental execution paths and restores the intended model:
1. LLM performs semantic authoring and semantic correction.
2. Deterministic code performs validation, routing, gating, retries, and reporting.
3. Deterministic code does not author transition prose, anchors, or inserted scene semantics.

## Doctrine Anchor
This plan is governed by:
1. `resources/plans/proposed/outline_pipeline_doctrine_manifesto_20260216_0205.md`

Locked doctrine statement:
1. LLM authors and lints; orchestrator never authors or discards; orchestrator only enforces validated state and deterministic invariants.

## Source Baseline
Primary base:
1. `resources/plans/proposed/outline_pipeline_refinement_plan_20260214_0615.md`

Reference only (extract good constraints, not implementation shape):
1. `resources/plans/failed/outline_pipeline_transition_quality_plan_20260214_1545.md`
2. `resources/plans/failed/outline_pipeline_strict_json_location_registry_plan_20260215_0510.md`
3. `resources/plans/failed/writing_loop_downstream_transition_hardening_plan_20260215_193219.md`
4. `resources/plans/failed/outline_registry_closure_phase_plan_20260216_000812.md`

## Locked Principles
1. Compiler-first prompt composition remains mandatory.
2. One-pass outline generation remains removed from production flow.
3. `outline generate` must support full rerun and phase rerun with deterministic dependency handling.
4. Scene and section transition quality is a primary gate, not a best-effort hint.
5. LLM is semantic authority for transition quality and inserted transition scenes.
6. Code must never paper over missing/invalid semantic fields with generated prose placeholders.
7. All failures, downgrades, and policy constraints must be visible in console and report artifacts.

## Corrected Pipeline Shape
The top-level pipeline remains six phases, but phase 04 is internally split into two LLM steps.

1. Phase 01: chapter spine
2. Phase 02: section architecture
3. Phase 03: scene draft (full outline v1.1 + required transition contract fields)
4. Phase 04A: transition seam analysis and candidate proposal (LLM)
5. Phase 04B: transition refinement and insertion execution (LLM)
6. Phase 05: cast function refinement
7. Phase 06: thread/payoff refinement

Note:
1. Phase 04A and 04B are one logical phase to the CLI (`phase_04_transition_causality_refinement`) but two explicit internal attempts/steps for orchestration and artifacting.
2. Code may select candidate edges deterministically only for routing; code may not inject semantic scene text.

## Role Separation Contract
### LLM responsibilities
1. Decide whether each seam should be inline bridge, micro scene, or full scene.
2. Author all inserted scene semantic content when insertion is required.
3. Author transition text and anchor content.
4. Rewrite invalid or low-quality transition semantics when routed by validator failures.

### Deterministic responsibilities
1. Validate schema, IDs, sequencing, link integrity, required fields, and policy constraints.
2. Compute and enforce insertion budget/tie-break routing signals.
3. Construct bounded retry directives with failing scene refs and field paths.
4. Gate progression, emit report artifacts, and block downstream writes on non-success status.

### Forbidden deterministic behavior
1. Creating fallback `transition_in_text` or `transition_out_text`.
2. Creating fallback anchors for transition fields.
3. Inserting synthetic transition scenes with generated summary/outcome/transition prose.
4. Silently rewriting seam resolution from model output without reason-coded visibility.

## Phase 04 Internal Two-Step Flow
### Step 04A: seam analysis (LLM)
Input:
1. Phase 03 outline artifact.
2. Transition hints payload.
3. Current policy settings (`strict_transition_bridges`, scene-count mode, insertion budget).

Output:
1. Full outline (may include seam metadata updates).
2. `phase_report` with candidate seam edges and rationale.
3. Candidate list must include scene refs, seam scores, and requested resolution classes.

### Step 04B: seam execution (LLM)
Input:
1. 04A output.
2. Deterministic candidate routing payload:
   - selected candidates under budget,
   - blocked candidates with reasons,
   - exact-count conflict notes when applicable.
3. Explicit instruction to author inserted scenes for selected candidates when resolution is `micro_scene` or `full_scene`.

Output:
1. Full updated outline with inserted scenes authored by LLM where required.
2. Updated phase report with:
   - inserted scene refs,
   - blocked_by_budget refs,
   - downgraded_resolution refs,
   - unresolved_required_insertions refs.

Hard rule:
1. If inserted scene is required and not authored by LLM, phase 04 fails.
2. No deterministic substitute scene content may be generated.

## Scene Count and Insertion Policy
Default mode:
1. `strong_non_exact` remains default.
2. Insertion is allowed under budget and policy.

Exact mode:
1. Insertion is disallowed unless explicitly approved by future policy.
2. If insertion is required for quality and exact mode is active, emit terminal conflict:
   - `exact_scene_count_transition_conflict`
3. Do not silently downgrade required insertion to inline bridge.

## Visibility and Write Gate
Every outline run must print:
1. Terminal status (`SUCCESS | SUCCESS_WITH_WARNINGS | PAUSED | ERROR`).
2. Phase/step where terminal status occurred.
3. Top reason codes.
4. Seam summary counts (inserted, blocked_by_budget, downgraded, unresolved_required_insertions).
5. Report path.

Write gate rules:
1. Writing is blocked when outline status is not `SUCCESS` or `SUCCESS_WITH_WARNINGS`.
2. Writing is also blocked when `requires_user_attention=true`.
3. `--ack-outline-issues` may bypass warnings only, never hard errors.
4. Terminal unresolved insertion requirement is always hard-block.

## Rerun and Resume Contract
1. Full rerun on existing outline is supported.
2. Phase rerun is supported with dependency checks.
3. Resume reuses successful phase outputs only when run fingerprint matches.
4. On mismatch, affected phase chain is invalidated and rerun.
5. Attempt artifacts and validation reports are retained per step (`04A`, `04B`).

## Artifact Contract
Run folder:
1. `outline/pipeline_runs/<run_id>/`

Required phase 04 artifacts:
1. `phase_04a_input.json`
2. `phase_04a_attempt_1.raw.json`
3. `phase_04a_output.json`
4. `phase_04a_validation.json`
5. `phase_04b_input.json`
6. `phase_04b_attempt_1.raw.json`
7. `phase_04b_output.json`
8. `phase_04b_validation.json`
9. `outline_transitions_refined_v1_1.json` (handoff artifact)

Run-level:
1. `outline_pipeline_report.json`
2. `outline_pipeline_decisions.json`
3. `outline_pipeline_latest.json`

## Prompt Contract Requirements
All phase prompts must include:
1. strict JSON response contract,
2. no placeholder identity tokens,
3. error contract (`error_v1`) for terminal failure shape,
4. timeline lock override for outlining mode.

Phase 04B prompt must additionally include:
1. explicit selected seam candidate list,
2. explicit instruction to author inserted scenes for selected candidates,
3. explicit prohibition against leaving selected insertions unresolved.

## Acceptance Criteria
1. No phase code creates transition prose or anchor text.
2. No phase code inserts semantic transition scenes with generated placeholder content.
3. Phase 04 selected insertion candidates are authored by LLM or the phase fails.
4. Exact-mode conflicts fail explicitly with reason code; no silent downgrade.
5. Console and report visibility includes seam decision outcomes.
6. Resume/rerun behavior remains deterministic and dependency-safe.
7. Prompt compiler remains sole prompt source of truth.

## Rollout Sequence
1. Rebuild plans and prompt contracts first.
2. Implement orchestration changes for split phase 04 (`04A`, `04B`).
3. Add validator/routing updates and remove semantic fallback code.
4. Add tests for insertion-required and conflict/failure paths.
5. Run end-to-end outline audits on test books.
6. Promote only after passing acceptance criteria.
