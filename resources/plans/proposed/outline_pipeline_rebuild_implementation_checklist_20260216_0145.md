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

### Tasks
1. Add internal 04A and 04B step orchestration under logical phase 04.
2. Add explicit per-step artifact writes (`phase_04a_*`, `phase_04b_*`).
3. Ensure rerun and resume can restart from 04A or 04B deterministically.
4. Ensure dependency checks prevent 04B execution without valid 04A output.
5. Preserve existing CLI external phase naming while documenting split behavior.

### Risks
1. Resume drift if step-level fingerprints are not tracked.
2. Confusing phase reporting unless report includes both step outcomes.

## Workstream B: Remove Semantic Fallbacks
### Files
1. `src/bookforge/outline.py`

### Tasks
1. Remove/replace any helpers that synthesize transition prose/anchors.
2. Remove/replace any code path that inserts semantic transition scenes directly.
3. Replace with reason-coded validation failures and retry routing.
4. Keep deterministic candidate routing logic only.

### Verification
1. Code search should show no live semantic fallback helpers for transition fields.
2. Tests should fail if fallback-like text appears without LLM authorship.

## Workstream C: Phase 04 Prompt Contracts
### Files
1. `resources/prompt_blocks/phase/outline_pipeline/phase_04_transition_causality_refinement_prompt_contract.md`
2. `resources/prompt_templates/outline_phase_04_transition_causality_refinement.md`
3. `resources/prompt_composition/manifests/outline_phase_04_transition_causality_refinement.composition.manifest.json`

### Tasks
1. Split contract into explicit 04A/04B sections or create two templates:
   - `outline_phase_04a_transition_seam_analysis.md`
   - `outline_phase_04b_transition_seam_execution.md`
2. 04A contract: candidate seam extraction with required candidate list fields.
3. 04B contract: selected candidates + explicit inserted scene authoring requirement.
4. Add hard prohibition on leaving selected insertions unresolved.
5. Add `error_v1` reason codes specific to 04A/04B failures.

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

### Tasks
1. register any new 04A/04B template names,
2. ensure workspace template distribution includes them,
3. recompose and refresh checksums,
4. update expected template counts/tests.

## Workstream G: Tests
### Files
1. `tests/test_outline_generate.py`
2. `tests/test_outline_transition_policy.py`
3. `tests/test_runner_outline_gate.py`
4. `tests/test_prompt_composition.py`

### Required tests
1. 04A candidates -> 04B inserted scenes success path.
2. 04B missing selected insertion -> retry -> terminal error.
3. 04B placeholder/meta transition text -> retry -> terminal error.
4. exact-count required insertion conflict -> terminal error.
5. blocked-by-budget candidates visible in report.
6. no deterministic semantic insertion occurred (regression guard).
7. resume from 04B uses valid 04A artifact and fingerprint checks.

## Workstream H: Audit Run Procedure
### Target
1. `workspace/books/criticulous_b1`

### Procedure
1. run full outline pipeline with non-exact default.
2. inspect phase 04 artifacts:
   - verify inserted scenes come from 04B LLM output, not code mutation.
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
