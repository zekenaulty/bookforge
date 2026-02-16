# Outline Pipeline Rebuild Implementation Checklist (20260216_0145)

## Purpose
Provide a concrete file-by-file execution checklist for rebuilding the outline refinement flow without repeating semantic fallback drift.

Use with:
1. `resources/plans/proposed/outline_pipeline_rebuild_plan_20260216_0145.md`
2. `resources/plans/proposed/outline_phase4_two_step_llm_transition_plan_20260216_0145.md`

## Doctrine Anchor
This checklist is governed by:
1. `resources/plans/proposed/outline_pipeline_doctrine_manifesto_20260216_0205.md`

Locked doctrine statement:
1. LLM authors and lints; orchestrator never authors or discards; orchestrator only enforces validated state and deterministic invariants.

## Global Implementation Rules
1. No deterministic semantic authoring for transition text, anchors, or inserted scene semantics.
2. LLM must author all semantic fixes.
3. Deterministic code may only validate, route, gate, and report.
4. Every policy action must be auditable by artifact.

## Workstream A: Orchestration and Phase 04 Split
### Files
1. `src/bookforge/outline.py`
2. `src/bookforge/cli.py`
3. `docs/help/outline_generate.md`
4. `src/bookforge/phases/outline/phase_01_chapter_spine.py` (new)
5. `src/bookforge/phases/outline/phase_02_section_architecture.py` (new)
6. `src/bookforge/phases/outline/phase_03_scene_draft.py` (new)
7. `src/bookforge/phases/outline/phase_04a_transition_seam_analysis.py` (new)
8. `src/bookforge/phases/outline/phase_04b_transition_execution.py` (new)
9. `src/bookforge/phases/outline/phase_05_cast_function_refinement.py` (new)
10. `src/bookforge/phases/outline/phase_06_thread_payoff_refinement.py` (new)
11. `src/bookforge/phases/outline/validators.py` (new)
12. `src/bookforge/phases/outline/artifacts.py` (new)
13. `src/bookforge/phases/outline/context.py` (new)

### Tasks
1. Convert outline pipeline to runner-style phase modules (`src/bookforge/phases/outline/*`).
2. Keep `src/bookforge/outline.py` as orchestration shell only.
3. Add internal 04A and 04B step orchestration under logical phase 04.
4. Add explicit per-step artifact writes (`phase_04a_*`, `phase_04b_*`).
5. Ensure rerun and resume can restart from 04A or 04B deterministically.
6. Ensure dependency checks prevent 04B execution without valid 04A output.
7. Preserve existing CLI external phase naming while documenting split behavior.

### Risks
1. Resume drift if step-level fingerprints are not tracked.
2. Confusing phase reporting unless report includes both step outcomes.
3. Partial refactor risk if phase logic remains duplicated between `outline.py` and new modules.

## Workstream B: Remove Semantic Fallbacks
### Files
1. `src/bookforge/outline.py`
2. `src/bookforge/phases/outline/phase_04b_transition_execution.py`
3. `src/bookforge/phases/outline/validators.py`

### Tasks
1. Remove/replace any helpers that synthesize transition prose/anchors.
2. Remove/replace any code path that inserts semantic transition scenes directly.
3. Replace with reason-coded validation failures and retry routing.
4. Keep deterministic candidate routing logic only.
5. Ensure fallback removal happens in phase modules, not only orchestrator shell.

### Verification
1. Code search should show no live semantic fallback helpers for transition fields.
2. Tests should fail if fallback-like text appears without LLM authorship.

## Workstream C: Phase 04 Prompt Contracts
### Files
1. `resources/prompt_blocks/phase/outline_pipeline/phase_04_transition_causality_refinement_prompt_contract.md` (04A source)
2. `resources/prompt_blocks/phase/outline_pipeline/phase_04b_transition_execution_prompt_contract.md` (new, 04B source)
3. `resources/prompt_templates/outline_phase_04a_transition_seam_analysis.md` (new/split)
4. `resources/prompt_templates/outline_phase_04b_transition_execution.md` (new)
5. `resources/prompt_composition/manifests/outline_phase_04a_transition_seam_analysis.composition.manifest.json` (new)
6. `resources/prompt_composition/manifests/outline_phase_04b_transition_execution.composition.manifest.json` (new)

### Tasks
1. Implement explicit 04A and 04B contract split.
2. 04A contract: candidate seam extraction with required candidate list fields.
3. 04B contract: selected candidates + explicit inserted scene authoring requirement.
4. Add hard prohibition on leaving selected insertions unresolved.
5. Add `error_v1` reason codes specific to 04A/04B failures.
6. Add explicit prompt language that inserted scenes must contain authored prose semantics, not fallback/meta phrasing.

### Compiler tasks
1. add/adjust manifests,
2. update allowlist tokens if step-specific placeholders are added,
3. recompose templates and refresh checksums.

## Workstream D: Validators and Routing
### Files
1. `src/bookforge/outline.py`
2. `schemas/outline.schema.json`
3. `schemas/error_v1.schema.json`
4. `schemas/outline_pipeline_report.schema.json`

### Tasks
1. Validate 04A candidate list shape and refs.
2. Validate 04B selected insertion resolution completeness.
3. Add explicit `unresolved_required_insertions` terminal failure.
4. Preserve existing link/sequence checks.
5. Preserve strict placeholder/meta detection as route-to-LLM fix, not auto-heal.
6. Ensure exact-count insertion conflicts are explicit and terminal.

## Workstream E: Reporting and Write Gate
### Files
1. `src/bookforge/outline.py`
2. `src/bookforge/runner.py`
3. `docs/help/run.md`
4. `docs/help/outline_generate.md`

### Tasks
1. Add seam decision summary to console and report:
   - candidate count,
   - selected count,
   - inserted count,
   - blocked_by_budget count,
   - unresolved_required_insertions count.
2. Ensure write gate blocks on non-success statuses and unresolved required insertion errors.
3. Ensure `--ack-outline-issues` does not bypass hard insertion failures.
4. Add operator-facing wording for ack behavior.

## Workstream F: Prompt Compiler Sync
### Files
1. `resources/prompt_composition/prompt_tokens_allowlist.json`
2. `resources/prompt_composition/source_of_truth_checksums.json`
3. `resources/prompt_composition/reports/compiled_trace/*`
4. `resources/prompt_composition/reports/compiled_debug/*`
5. `src/bookforge/workspace.py`
6. `tests/test_prompt_composition.py`
7. `resources/prompt_composition/manifests/outline_phase_04a_transition_seam_analysis.composition.manifest.json`
8. `resources/prompt_composition/manifests/outline_phase_04b_transition_execution.composition.manifest.json`

### Tasks
1. register new 04A/04B template names and manifest ids,
2. ensure workspace template distribution includes them,
3. recompose and refresh checksums,
4. update expected template counts/tests.
5. ensure 04B placeholder inputs are compiler-allowlisted (selected/blocked/policy payload blocks).

## Workstream G: Tests
### Files
1. `tests/test_outline_generate.py`
2. `tests/test_outline_transition_policy.py`
3. `tests/test_runner_outline_gate.py`
4. `tests/test_prompt_composition.py`
5. `tests/test_outline_phase4_prompt_render.py` (new)
6. `tests/test_outline_phase_module_dispatch.py` (new)

### Required tests
1. 04A candidates -> 04B inserted scenes success path.
2. 04B missing selected insertion -> retry -> terminal error.
3. 04B placeholder/meta transition text -> retry -> terminal error.
4. exact-count required insertion conflict -> terminal error.
5. blocked-by-budget candidates visible in report.
6. no deterministic semantic insertion occurred (regression guard).
7. resume from 04B uses valid 04A artifact and fingerprint checks.
8. 04B prompt render includes selected/blocked/policy payload blocks (no missing placeholders at runtime).
9. Orchestrator dispatches through module handlers; phase logic is not embedded in `outline.py`.

## Workstream H: Audit Run Procedure
### Target
1. `workspace/books/criticulous_b1`

### Procedure
1. run full outline pipeline with non-exact default.
2. inspect phase 04 artifacts:
   - verify inserted scenes come from 04B LLM output, not code mutation.
   - verify `phase_04_selected_candidates.json` and `phase_04_policy_context.json` match rendered 04B prompt payload.
3. run exact-count mode and confirm explicit conflict behavior.
4. run rerun/resume cases and confirm deterministic behavior.
5. produce audit report with:
   - failures,
   - blocked candidates,
   - quality observations,
   - action items.

## Completion Gates
1. No semantic fallback insertion code remains.
2. Phase 04 insertion semantics are fully LLM-authored.
3. Report visibility is complete and actionable.
4. Tests cover old failure class and new expected behavior.
5. CLI/docs reflect actual operator controls.
6. Outline phase business logic lives in phase-specific modules, with `outline.py` acting as thin orchestrator.

## Ramifications Summary (Reviewer-Facing)
1. Prompt surface area increases:
   - +1 prompt-block contract (04B),
   - +2 compiled phase-04 templates (04A/04B),
   - +2 composition manifests.
2. Runtime artifact volume increases with step-split trace files and routing payload artifacts.
3. Outline run latency may increase due to extra 04B step and retries.
4. Failure visibility improves but will produce more explicit terminal errors during early tuning.
5. Deterministic code complexity shifts from semantic patching to routing/reporting validation.

## Explicit Non-Goals (This Rebuild)
1. No writing-loop redesign in this implementation pass.
2. No character-from-prose promotion pipeline in this implementation pass.
3. No location registry runtime migration beyond outline-phase needs in this implementation pass.
4. No restoration of one-pass outline generation path.
