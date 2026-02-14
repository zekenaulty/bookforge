# Outline Pipeline Refinement Plan (20260214_0615)

## Objective
Implement a deterministic, auditable, multi-phase outline pipeline that improves transition quality, section coherence, and cast/thread structure while preserving runtime stability and schema compatibility.

## Locked User Scope
1. Re-run the full outline cycle on an existing outline via `outline generate`.
2. Re-run specific outline phases via `outline generate`.
3. Raise quality at scene/section edges, including required author-provided transition hints.
4. Use the prompt compiler/composition system as the only prompt source-of-truth path for this work.

## Non-Negotiable Architecture
- Build-time prompt composition remains authoritative.
- Runtime still consumes flat template files under `prompts/templates/*.md`.
- No direct ad hoc prompt strings in phase code.
- Outline pipeline prompts must be compiler-managed blocks + manifests.

## Current-State Cross-Reference (Code Coupling)
### Outline generation and CLI
- `src/bookforge/cli.py`
  - `outline generate` currently supports one-pass generation with `--new-version` and `--prompt-file`.
- `src/bookforge/outline.py`
  - `generate_outline` is single-pass and writes `outline/outline.json` directly.
  - Existing `outline.json` blocks regeneration unless `--new-version`.

### Downstream consumers affected by outline semantics
- `src/bookforge/phases/plan.py`
  - `_build_outline_window` derives `previous/current/next` scene context.
  - `plan_scene` builds scene-card inputs from outline structure.
- `src/bookforge/pipeline/outline.py`
  - chapter/scene order and scene count derivation utilities.
- `src/bookforge/runner.py`
  - cursor progression and chapter compile rely on outline ordering.
- `src/bookforge/pipeline/scene.py`
  - scene cast derivation depends on outline scene fields.
- `src/bookforge/memory/durable_state.py`
  - thread/device derivations depend on outline threads and references.

### Prompt compiler and template distribution coupling
- `src/bookforge/prompt/composition.py`
  - manifest schema enforcement, allowlist enforcement, deterministic compose, trace/debug reports.
  - active manifest discovery is top-level only: `resources/prompt_composition/manifests/*.composition.manifest.json`.
- `resources/prompt_composition/manifest.schema.json`
  - manifest contract and guard/risk/repeat policy.
- `resources/prompt_composition/prompt_tokens_allowlist.json`
  - unknown token hard-fail gate.
- `resources/prompt_composition/source_of_truth_checksums.json`
  - composed output integrity gate.
- `src/bookforge/workspace.py`
  - `PROMPT_TEMPLATE_FILES` controls what compiled templates are copied into each book workspace.
- `tests/test_prompt_composition.py`
  - currently assumes 14 compiled templates; will need update when new templates activate.

## Transition Gap (Why This Plan Exists)
- Current one-pass outline generation can produce schema-valid but weak scene handoffs.
- Observed failure mode: abrupt location shifts and unconsumed outcomes between consecutive scenes.
- Root issue: no required edge semantics in outline generation, and no transition-focused refinement pass.

## Compiler-First Implementation Strategy
This plan adds new outline-phase templates as compiler-managed assets, but keeps them in a **non-active draft lane** until review approval.

### Draft prompt block files (created)
- `resources/prompt_blocks/phase/outline_pipeline/phase_01_chapter_spine_prompt_contract.md`
- `resources/prompt_blocks/phase/outline_pipeline/phase_02_section_architecture_prompt_contract.md`
- `resources/prompt_blocks/phase/outline_pipeline/phase_03_scene_draft_prompt_contract.md`
- `resources/prompt_blocks/phase/outline_pipeline/phase_04_transition_causality_refinement_prompt_contract.md`
- `resources/prompt_blocks/phase/outline_pipeline/phase_05_cast_function_refinement_prompt_contract.md`
- `resources/prompt_blocks/phase/outline_pipeline/phase_06_thread_payoff_refinement_prompt_contract.md`

### Draft manifests (non-active, created)
- `resources/prompt_composition/manifests/proposed/outline_phase_01_chapter_spine.composition.manifest.json`
- `resources/prompt_composition/manifests/proposed/outline_phase_02_section_architecture.composition.manifest.json`
- `resources/prompt_composition/manifests/proposed/outline_phase_03_scene_draft.composition.manifest.json`
- `resources/prompt_composition/manifests/proposed/outline_phase_04_transition_causality_refinement.composition.manifest.json`
- `resources/prompt_composition/manifests/proposed/outline_phase_05_cast_function_refinement.composition.manifest.json`
- `resources/prompt_composition/manifests/proposed/outline_phase_06_thread_payoff_refinement.composition.manifest.json`

### Why non-active first
- Active discovery only reads top-level manifests.
- Keeping manifests in `manifests/proposed/` allows full review without changing current compiled runtime templates.
- Promotion to active is explicit and auditable.

## Semantically Meaningful Naming Contract
### Template names (compiled outputs after activation)
- `outline_phase_01_chapter_spine.md`
- `outline_phase_02_section_architecture.md`
- `outline_phase_03_scene_draft.md`
- `outline_phase_04_transition_causality_refinement.md`
- `outline_phase_05_cast_function_refinement.md`
- `outline_phase_06_thread_payoff_refinement.md`

### Naming policy
- Phase number + intent + object are required in names.
- No generic `seg_01` style names in production prompt sources.
- `semantic_id` in manifests must remain stable even if paths move.

## Outline Pipeline V2 (Deterministic 6-Phase Flow)
Each phase is JSON-only, max 2 attempts, reason-coded error on second failure.

1. `phase_01_chapter_spine`
- Prompt: `outline_phase_01_chapter_spine.md`
- Output artifact: `outline_spine_v1.json`
- Scope: chapter goals/roles/stakes/bridges/pacing only.

2. `phase_02_section_architecture`
- Prompt: `outline_phase_02_section_architecture.md`
- Output artifact: `outline_sections_v1.json`
- Scope: section mini-arc structure and target scene counts.

3. `phase_03_scene_draft`
- Prompt: `outline_phase_03_scene_draft.md`
- Output artifact: `outline_draft_v1_1.json`
- Scope: first full outline v1.1 draft with optional edge fields.

4. `phase_04_transition_causality_refinement`
- Prompt: `outline_phase_04_transition_causality_refinement.md`
- Output artifact: `outline_refined_transitions_v1_1.json`
- Scope: enforce outcome-consumption continuity and transition quality.

5. `phase_05_cast_function_refinement`
- Prompt: `outline_phase_05_cast_function_refinement.md`
- Output artifact: `outline_refined_cast_v1_1.json`
- Scope: recurring role utility, intro correctness, cast compression.

6. `phase_06_thread_payoff_refinement`
- Prompt: `outline_phase_06_thread_payoff_refinement.md`
- Output artifact: `outline_final_v1_1.json`
- Scope: thread cadence/escalation/payoff and chapter bridge alignment.

Final promote:
- `outline_final_v1_1.json` -> `outline/outline.json`
- refresh chapter shards + `outline/characters.json`.

## CLI Contract Expansion (Required)
Extend `bookforge outline generate`:
- `--rerun`
- `--from-phase <phase_id>`
- `--to-phase <phase_id>`
- `--phase <phase_id>` (single phase alias)
- `--transition-hints-file <path>`
- `--strict-transition-hints`
- optional: `--force-rerun-with-draft` (explicit unsafe override)

Compatibility:
- Existing `outline generate --book <id>` continues to work.
- Existing `--new-version` archive behavior remains.

## Deterministic Validation Gates (Must Implement)
### Phase-level gates
- Schema validity for each phase artifact.
- ID integrity and reference integrity.
- Intro integrity (`introduces`, first appearance, character intro stub alignment).
- Outcome concreteness.
- Transition consumption (no orphan outcomes at phase 04+).
- Section intent closure.
- Thread touch and escalation heuristics.
- Chapter bridge alignment.

### Pipeline-level gates
- Max 2 attempts per phase.
- On second failure emit `ERROR` JSON with `phase`, `reasons`, and validator evidence.
- Block final promote when any hard gate fails.

## Prompt Compiler Activation Plan (After Review Approval)
1. Promote manifests from `resources/prompt_composition/manifests/proposed/` to `resources/prompt_composition/manifests/`.
2. Add allowlist tokens in `resources/prompt_composition/prompt_tokens_allowlist.json`:
- `{{transition_hints}}`
- `{{outline_spine_v1}}`
- `{{outline_sections_v1}}`
- `{{outline_draft_v1_1}}`
- `{{outline_transitions_refined_v1_1}}`
- `{{outline_cast_refined_v1_1}}`
3. Update `src/bookforge/workspace.py` `PROMPT_TEMPLATE_FILES` to include six new outline phase templates.
4. Compose templates and update `resources/prompt_composition/source_of_truth_checksums.json`.
5. Update tests for new template count and coverage:
- `tests/test_prompt_composition.py`
- add outline pipeline tests for rerun/phase rerun behavior.
6. Regenerate book prompts with `book update-templates`.

## Planner and Consumer Upgrades Required
### `src/bookforge/phases/plan.py`
- Extend outline window payload to include edge fields:
  - `transition_in`, `transition_out`, `edge_intent`, `consumes_outcome_from`, `hands_off_to`
- Ensure planner consumes transition hints and projects them into scene-card fields:
  - `transition_type`, `constraints`, `end_condition`, callback/thread continuity.

### `src/bookforge/outline.py`
- Replace one-pass generation with phase orchestration.
- Add rerun safety checks for existing draft artifacts.
- Persist per-phase artifacts and validation logs.

### `docs/help/outline_generate.md`
- Update flags and rerun behavior docs.

## Logging and Traceability (Mandatory)
Persist under:
- `workspace/books/<book_id>/outline/pipeline_runs/<run_id>/`

Per phase:
- `phase_0N_input.json`
- `phase_0N_output.json`
- `phase_0N_validation.json`
- `phase_0N_attempt_1.raw.json`
- `phase_0N_attempt_2.raw.json` when used

Run-level:
- `outline_pipeline_report.json`
- `outline_pipeline_decisions.json`
- `outline_pipeline_latest.json`

Prompt compiler traceability remains mandatory:
- `resources/prompt_composition/reports/compiled_trace/*.trace.json`
- `resources/prompt_composition/reports/compiled_debug/*.md`
- `resources/prompt_composition/reports/placeholder_audit/*.json`

## Risk Register (Focused)
1. Outline rerun over existing drafted scenes can invalidate continuity.
- Mitigation: block by default, require explicit override.

2. Transition hints missing/weak can collapse phase 04 quality.
- Mitigation: `--strict-transition-hints` + validator hard fail.

3. New phase tokens fail compose due allowlist mismatch.
- Mitigation: allowlist update is activation gate, not optional.

4. New templates exist but are not copied to book workspaces.
- Mitigation: update `PROMPT_TEMPLATE_FILES` in same change.

5. Active manifest expansion breaks checksum/test expectations.
- Mitigation: update checksums + tests in same PR; no partial activation.

6. Phase rerun causes hidden downstream incoherence.
- Mitigation: downstream invalidation and forced re-validation sweep before promote.

## Test Plan (Pre-Merge)
1. Compiler contract checks
- manifest schema validation for new manifests.
- placeholder allowlist pass.
- deterministic compose pass.

2. Outline pipeline behavior
- fresh run full six phases.
- rerun full cycle on existing outline.
- single-phase rerun for phase 04 and phase 05.

3. Safety and edge tests
- rerun blocked when drafted scenes exist (without override).
- strict transition hint mode failure and success cases.
- orphan-outcome detection catches seeded failure case.

4. Downstream compatibility
- `plan_scene` still produces valid scene cards.
- run loop cursor progression unchanged on final promoted outline.

## Review Package (This Pass)
Reviewer can inspect:
- this plan file,
- six new phase prompt blocks,
- six proposed manifests,
- unchanged active runtime manifests/templates (no activation yet).

## Definition of Done
- Outside reviewer signs off on prompt contracts, naming, and activation strategy.
- Activation PR updates manifests/allowlist/checksums/template distribution/tests together.
- Full outline rerun and phase rerun work deterministically.
- Transition quality gate is enforced and measurable.
- No regressions in planner, runner progression, or schema validation.

