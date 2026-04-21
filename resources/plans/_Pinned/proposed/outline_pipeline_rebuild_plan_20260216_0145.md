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

## Code Architecture Lock (Runner-Style Phase Modules)
To prevent monolithic drift:
1. `src/bookforge/outline.py` is orchestration shell only.
2. Outline phase execution logic must live in phase-specific modules, mirroring runner phase style.
3. Recommended module root:
   - `src/bookforge/phases/outline/`
4. Required phase modules:
   - `src/bookforge/phases/outline/phase_01_chapter_spine.py`
   - `src/bookforge/phases/outline/phase_02_section_architecture.py`
   - `src/bookforge/phases/outline/phase_03_scene_draft.py`
   - `src/bookforge/phases/outline/phase_04a_transition_seam_analysis.py`
   - `src/bookforge/phases/outline/phase_04b_transition_execution.py`
   - `src/bookforge/phases/outline/phase_04c_metadata_relink.py`
   - `src/bookforge/phases/outline/phase_04c_intro_sync.py`
   - `src/bookforge/phases/outline/phase_04c_handoff_normalize.py`
   - `src/bookforge/phases/outline/phase_04d_seam_hygiene.py`
   - `src/bookforge/phases/outline/phase_05_cast_function_refinement.py`
   - `src/bookforge/phases/outline/phase_06_thread_payoff_refinement.py`
5. Shared cross-phase helpers belong in dedicated modules, not `outline.py`:
   - `src/bookforge/phases/outline/validators.py`
   - `src/bookforge/phases/outline/artifacts.py`
   - `src/bookforge/phases/outline/context.py`
6. Any growth pattern that trends `outline.py` toward monolith size is a design failure and must be refactored before merge.

## Corrected Pipeline Shape
The top-level pipeline remains six phases, but phase 04 is internally split into two LLM steps.

1. Phase 01: chapter spine
2. Phase 02: section architecture
3. Phase 03: scene draft (full outline v1.1 + required transition contract fields)
4. Phase 04A: transition seam analysis and candidate proposal (LLM)
5. Phase 04B: transition refinement and insertion execution (LLM)
6. Phase 04C: metadata relink for insertion drift (LLM)
7. Phase 04C-Intro: character intro sync (LLM)
8. Phase 04C-Handoff: chapter-terminal + location jump normalization (LLM)
9. Phase 04D: seam hygiene (LLM)
10. Phase 05: cast function refinement
11. Phase 06: thread/payoff refinement

Note:
1. Phase 04A/04B/04C/04C-Intro/04C-Handoff/04D are one logical phase to the CLI (`phase_04_transition_causality_refinement`) but explicit internal steps for orchestration and artifacting.
2. Code may select candidate edges deterministically only for routing; code may not inject semantic scene text.

## Prompt Asset Delta (Explicit)
Current prompt-block directory already contains:
1. `resources/prompt_blocks/phase/outline_pipeline/phase_04_transition_causality_refinement_prompt_contract.md`

Required additions/changes:
1. Treat existing file as phase 04A contract source (seam analysis contract).
2. Add new phase 04B contract file:
   - `resources/prompt_blocks/phase/outline_pipeline/phase_04b_transition_execution_prompt_contract.md`
3. Add new phase 04C contract file:
   - `resources/prompt_blocks/phase/outline_pipeline/phase_04c_metadata_relink_prompt_contract.md`
4. Add new phase 04C-Intro contract file:
   - `resources/prompt_blocks/phase/outline_pipeline/phase_04c_intro_sync_prompt_contract.md`
5. Add new phase 04C-Handoff contract file:
   - `resources/prompt_blocks/phase/outline_pipeline/phase_04c_handoff_normalize_prompt_contract.md`
6. Add new phase 04D contract file:
   - `resources/prompt_blocks/phase/outline_pipeline/phase_04d_seam_hygiene_prompt_contract.md`
7. Add or split composed prompt templates:
   - `resources/prompt_templates/outline_phase_04a_transition_seam_analysis.md`
   - `resources/prompt_templates/outline_phase_04b_transition_execution.md`
   - `resources/prompt_templates/outline_phase_04c_metadata_relink.md`
   - `resources/prompt_templates/outline_phase_04c_intro_sync.md`
   - `resources/prompt_templates/outline_phase_04c_handoff_normalize.md`
   - `resources/prompt_templates/outline_phase_04d_seam_hygiene.md`
8. Add new composition manifests:
   - `resources/prompt_composition/manifests/outline_phase_04a_transition_seam_analysis.composition.manifest.json`
   - `resources/prompt_composition/manifests/outline_phase_04b_transition_execution.composition.manifest.json`
   - `resources/prompt_composition/manifests/outline_phase_04c_metadata_relink.composition.manifest.json`
   - `resources/prompt_composition/manifests/outline_phase_04c_intro_sync.composition.manifest.json`
   - `resources/prompt_composition/manifests/outline_phase_04c_handoff_normalize.composition.manifest.json`
   - `resources/prompt_composition/manifests/outline_phase_04d_seam_hygiene.composition.manifest.json`
9. Keep legacy template compatibility for operator-facing phase naming:
   - `outline_phase_04_transition_causality_refinement` remains CLI logical phase ID.
   - Runtime can map this to internal steps `04A` and `04B`.

## Prompt Input Wiring (04B)
Phase 04B prompt must receive explicit deterministic routing payload from orchestrator:
1. selected seam candidates,
2. blocked candidates and reasons,
3. scene-count policy mode,
4. insertion budget context,
5. exact-mode conflict markers.

Recommended placeholder payload blocks:
1. `{{outline_phase_04a_output}}`
2. `{{phase_04_selected_candidates_json}}`
3. `{{phase_04_blocked_candidates_json}}`
4. `{{phase_04_policy_context_json}}`

Compiler allowlist must be updated for whichever placeholders are adopted.

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

## Phase 04 Internal Multi-Step Flow
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
   - insertion edge impacts,
   - blocked_by_budget refs,
   - downgraded_resolution refs,
   - unresolved_required_insertions refs.

Hard rule:
1. If inserted scene is required and not authored by LLM, phase 04 fails.
2. No deterministic substitute scene content may be generated.

### Step 04C: metadata relink (LLM)
Input:
1. 04B output.
2. Impact windows derived from 04B insertion_edge_impacts.
3. Allowed-fields contract (structural only).

Output:
1. Full updated outline with structural relink fixes applied in-window.
2. Updated phase report with touched refs/fields and intro updates.

Hard rule:
1. No scene add/remove/reorder or scene_id changes.
2. Only window refs and allowed fields may change.

### Step 04C-Intro: character intro sync (LLM)
Input:
1. 04C output.
2. Chapter-local list of character ids whose `intro` is stale.
3. Authoritative character registry snapshot.

Output:
1. Chapter outline unchanged.
2. Character registry with corrected `intro` entries for listed ids only.

Hard rule:
1. No scene changes and no character add/remove.
2. Only `characters[*].intro` for listed ids may change.

### Step 04C-Handoff: handoff normalize (LLM)
Input:
1. 04C-Intro output.
2. Chapter-local handoff fix list (scene refs + reason).
3. Allowed location-jump modes list.

Output:
1. Chapter outline with `handoff_mode` updated for listed refs only.
2. Phase report of touched refs.

Hard rule:
1. Only `handoff_mode` may change on listed refs.
2. Chapter-final scenes must be `handoff_mode=terminal`.
3. Location jumps must use `arrival_checkpoint` or `time_skip` unless the scene is terminal.

### Step 04D: seam hygiene (LLM)
Input:
1. 04C-Handoff output.
2. Window list derived from insertion impacts + missing seam metadata + identical anchors.
3. Allowed seam/transition fields list (authoritative).

Output:
1. Chapter outline with seam metadata and anchors repaired in-window.
2. Phase report with touched refs/fields.

Hard rule:
1. Seam metadata (`seam_score`, `seam_resolution`) required on every scene.
2. Successor transition_in anchors must reflect the true predecessor after insertion.
3. No scene add/remove/reorder or registry changes.

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
9. `phase_04c_input.json`
10. `phase_04c_attempt_1.raw.json`
11. `phase_04c_output.json`
12. `phase_04c_validation.json`
13. `outline_transitions_refined_v1_1.json` (handoff artifact, post-04B)
14. `outline_transitions_relinked_v1_1.json` (handoff artifact, post-04C)

Phase 04 step-split trace artifacts:
1. `phase_04_selected_candidates.json`
2. `phase_04_blocked_candidates.json`
3. `phase_04_policy_context.json`
4. `phase_04_transition_decision_trace.json`

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

## Implementation Touchpoint Matrix (Formalized)
1. `src/bookforge/outline.py`
   - keep as thin orchestrator only,
   - dispatch phases to `src/bookforge/phases/outline/*`,
   - no embedded per-phase business logic.
2. `src/bookforge/cli.py`
   - preserve logical phase naming, expose docs/help for internal 04A/04B split behavior.
3. `src/bookforge/phases/outline/phase_01_chapter_spine.py` (new)
   - phase 01 execution logic.
4. `src/bookforge/phases/outline/phase_02_section_architecture.py` (new)
   - phase 02 execution logic.
5. `src/bookforge/phases/outline/phase_03_scene_draft.py` (new)
   - phase 03 execution logic.
6. `src/bookforge/phases/outline/phase_04a_transition_seam_analysis.py` (new)
   - phase 04A execution logic.
7. `src/bookforge/phases/outline/phase_04b_transition_execution.py` (new)
   - phase 04B execution logic and insertion-resolution validation handoff.
8. `src/bookforge/phases/outline/phase_04c_metadata_relink.py` (new)
   - phase 04C metadata relink execution logic.
9. `src/bookforge/phases/outline/phase_05_cast_function_refinement.py` (new)
   - phase 05 execution logic.
10. `src/bookforge/phases/outline/phase_06_thread_payoff_refinement.py` (new)
   - phase 06 execution logic.
10. `src/bookforge/phases/outline/validators.py` (new)
   - shared deterministic validators.
11. `src/bookforge/phases/outline/artifacts.py` (new)
   - artifact read/write and step report helpers.
12. `src/bookforge/phases/outline/context.py` (new)
   - shared render input/context assembly.
13. `resources/prompt_blocks/phase/outline_pipeline/phase_04_transition_causality_refinement_prompt_contract.md`
   - treat as 04A contract source.
14. `resources/prompt_blocks/phase/outline_pipeline/phase_04b_transition_execution_prompt_contract.md` (new)
   - define 04B insertion execution and inserted-scene authoring contract.
15. `resources/prompt_blocks/phase/outline_pipeline/phase_04c_metadata_relink_prompt_contract.md` (new)
   - define 04C metadata relink contract.
16. `resources/prompt_templates/outline_phase_04a_transition_seam_analysis.md` (new/split)
   - compiled 04A template.
17. `resources/prompt_templates/outline_phase_04b_transition_execution.md` (new)
   - compiled 04B template.
18. `resources/prompt_templates/outline_phase_04c_metadata_relink.md` (new)
   - compiled 04C template.
19. `resources/prompt_composition/manifests/outline_phase_04a_transition_seam_analysis.composition.manifest.json` (new)
   - compose 04A template from blocks.
20. `resources/prompt_composition/manifests/outline_phase_04b_transition_execution.composition.manifest.json` (new)
   - compose 04B template from blocks.
21. `resources/prompt_composition/manifests/outline_phase_04c_metadata_relink.composition.manifest.json` (new)
   - compose 04C template from blocks.
22. `resources/prompt_composition/prompt_tokens_allowlist.json`
   - allowlist 04B/04C routing + window payload placeholders.
23. `resources/prompt_composition/source_of_truth_checksums.json`
   - refresh checksums after prompt asset changes.
21. `src/bookforge/workspace.py`
   - include new templates in workspace distribution.
22. `schemas/outline.schema.json`, `schemas/error_v1.schema.json`, `schemas/outline_pipeline_report.schema.json`
   - ensure step outputs and error/report contracts are schema-valid and testable.
23. `tests/test_outline_generate.py`, `tests/test_outline_transition_policy.py`, `tests/test_prompt_composition.py`, `tests/test_runner_outline_gate.py`
   - add regression coverage for 04A/04B split and no-fallback guarantees.
24. `docs/help/outline_generate.md`, `docs/help/run.md`
   - operator behavior, gating semantics, and 04A/04B visibility.

## Formalization Gate
No implementation should begin until reviewers sign off on:
1. phase 04A/04B/04C prompt asset names and locations,
2. 04B/04C routing + window payload placeholders,
3. failure/gating behavior for unresolved required insertions,
4. exact-mode conflict behavior.

## Acceptance Criteria
1. No phase code creates transition prose or anchor text.
2. No phase code inserts semantic transition scenes with generated placeholder content.
3. Phase 04 selected insertion candidates are authored by LLM or the phase fails.
4. Phase 04C relink touches only window refs and allowed fields.
5. Exact-mode conflicts fail explicitly with reason code; no silent downgrade.
6. Console and report visibility includes seam decision outcomes.
7. Resume/rerun behavior remains deterministic and dependency-safe.
8. Prompt compiler remains sole prompt source of truth.

## Rollout Sequence
1. Rebuild plans and prompt contracts first.
2. Scaffold runner-style outline phase module package and move phase business logic out of `outline.py`.
3. Implement prompt asset split for phase 04A/04B (blocks/templates/manifests/checksums).
4. Implement orchestration changes for split phase 04 (`04A`, `04B`).
5. Add validator/routing updates and remove semantic fallback code.
6. Add tests for insertion-required, module dispatch, and conflict/failure paths.
7. Run end-to-end outline audits on test books.
8. Promote only after passing acceptance criteria.
