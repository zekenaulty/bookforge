# Outline Pipeline Refinement Plan (20260214_0615)

## Objective
Implement a deterministic, auditable, compiler-first multi-phase outline pipeline that improves scene transitions, section coherence, and cast/thread integrity while preserving runtime compatibility with existing BookForge flows.

## Locked Scope
1. Re-run full outline cycle on existing outlines via `outline generate`.
2. Re-run specific outline phases via `outline generate`.
3. Improve scene and section edge continuity with explicit transition intent support.
4. Keep prompt compiler/composition as the only prompt source-of-truth path.
5. Support full `--resume` behavior for outline pipeline runs with parity to main `run --resume` behavior.

## Decision Locks (User Confirmed 2026-02-14)
1. One-pass outline generation is removed from default and compatibility modes for this feature track.
2. Scene-count enforcement policy:
- enforce chapter-level `expected_scene_count` strongly by default in outline pipeline validation.
- support author-controlled range mode for scene-count targets, with high-end bias when selecting within range.
- provide explicit command flag `--exact-scene-count` to force exact strict matching behavior when configured.
3. Handoff/heuristic strictness policy:
- warning-by-default, with explicit parameter override to strict error mode.
4. `--prompt-file` remains supported only as structured input into composed templates.
5. `--force-rerun-with-draft` remains a hard explicit flag and must be fully documented in help docs.

## Operational Compatibility Boundary (Explicit)
`outline generate --book <id>` continues to work means:
- the same CLI entrypoint remains valid,
- the final promoted artifact remains `outline/outline.json` in schema `1.1` compatible shape,
- the execution engine is the 6-phase orchestrator.

Legacy one-pass behavior policy:
- one-pass is removed for outline pipeline v2 scope.
- no legacy one-pass fallback path is included in this implementation scope.

`--prompt-file` policy under compiler-first rules:
- `--prompt-file` remains supported as structured input data only (mapped to `{{user_prompt}}` in composed templates),
- no ad hoc non-composed instruction text may be appended in phase code.

## Determinism Contract (Input vs Output)
### Input determinism fingerprint (must be computed and stored)
The pipeline run fingerprint must include hashes of:
- `book.json` (or normalized planning-relevant subset),
- `targets`,
- `user_prompt` and `notes`,
- transition hints payload,
- active composed template checksums for all outline pipeline phase templates,
- orchestrator settings affecting behavior (`--from-phase`, `--to-phase`, strict flags, exact-count mode),
- prior phase handoff artifact hashes when starting from phase `N > 1`.

### Output determinism expectations
With unchanged fingerprint and resume-enabled reuse:
- previously successful phase outputs are reused byte-for-byte.

With unchanged fingerprint and fresh rerun:
- structural fields must remain stable:
  - `chapter_id` ordering,
  - chapter-local `scene_id` ordering,
  - reference graph shape (`consumes_outcome_from`, `hands_off_to`),
  - section closure anchors (`end_condition` / `end_condition_echo`),
  - top-level registry id sets (`characters`, `threads`) when referenced.
- lexical content may vary unless constrained by stricter configured policies.

## Approved Refinements Added In This Revision
The following items are now explicitly adopted and treated as release requirements:

1. Add `section.end_condition` in phase 02 and require section-final scene anchoring/echoing for deterministic closure checks.
2. Require sequential `chapter_id` policy and monotonic chapter-local `scene_id` policy explicitly.
3. Require top-level `threads` and `characters` arrays whenever scene-level references require them (instead of "recommended only").

## Adoption Lock Verification (No-Drift Policy)
These three items are treated as locked acceptance criteria and must be represented in:
- prompt contracts,
- deterministic validators,
- phase reports,
- tests,
- reviewer checklist.

Verification mapping:
1. `section.end_condition` + section-final anchoring
- Prompt contract coverage: phase 02 defines `end_condition`; phase 03+ enforces `end_condition_echo`.
- Validator coverage: section closure gates require both fields and match policy.
- Test coverage: missing/empty/mismatch cases must fail deterministically.

2. Sequential `chapter_id` + monotonic chapter-local `scene_id`
- Prompt contract coverage: phase 01 and phase 03 define sequencing policy explicitly.
- Validator coverage: hard fail on gaps, duplicates, non-integer ids, non-monotonic progression.
- Test coverage: seeded non-sequential inputs must fail.

3. Required top-level registry arrays when referenced
- Prompt contract coverage: phase 03+ requires `characters`/`threads` arrays whenever scene references exist.
- Validator coverage: hard fail for missing registry arrays or missing referenced ids.
- Test coverage: referenced-id-without-registry and unknown-id cases must fail.

## Non-Negotiable Architecture
- Build-time composition remains authoritative.
- Runtime continues reading flat templates from `prompts/templates/*.md`.
- No ad hoc prompt strings embedded in orchestration code.
- New outline-phase prompts are managed through compiler manifests and prompt blocks.

## Current-State Cross-Reference (Code Coupling)
### Generation and CLI surfaces
- `src/bookforge/cli.py`
  - Current `outline generate` supports one-pass generation with `--new-version` and `--prompt-file`.
- `src/bookforge/outline.py`
  - Current `generate_outline` is one-pass and writes `outline/outline.json`.
  - Existing outline blocks regeneration unless `--new-version`.

### Downstream consumers affected by outline semantics
- `src/bookforge/phases/plan.py`
  - `_build_outline_window` and `plan_scene` depend on outline ordering and scene structure.
- `src/bookforge/pipeline/outline.py`
  - Chapter/scene ordering helpers and summary functions.
- `src/bookforge/runner.py`
  - Cursor and chapter compilation depend on stable outline sequencing.
- `src/bookforge/pipeline/scene.py`
  - Cast derivation depends on scene character references.
- `src/bookforge/memory/durable_state.py`
  - Thread/device derivation depends on outline thread references.

### Prompt compiler coupling
- `src/bookforge/prompt/composition.py`
  - Manifest contract enforcement, placeholder allowlist, deterministic compose, trace/debug reports.
  - Active manifest discovery only reads `resources/prompt_composition/manifests/*.composition.manifest.json`.
- `resources/prompt_composition/manifest.schema.json`
  - Guard/risk/repeat schema contract.
- `resources/prompt_composition/prompt_tokens_allowlist.json`
  - Unknown token hard-fail.
- `resources/prompt_composition/source_of_truth_checksums.json`
  - Composed output integrity.
- `src/bookforge/workspace.py`
  - `PROMPT_TEMPLATE_FILES` controls template distribution into book workspaces.

## Compiler-First Prompt Assets (Current Drafts)
### Draft prompt blocks (already created)
- `resources/prompt_blocks/phase/outline_pipeline/phase_01_chapter_spine_prompt_contract.md`
- `resources/prompt_blocks/phase/outline_pipeline/phase_02_section_architecture_prompt_contract.md`
- `resources/prompt_blocks/phase/outline_pipeline/phase_03_scene_draft_prompt_contract.md`
- `resources/prompt_blocks/phase/outline_pipeline/phase_04_transition_causality_refinement_prompt_contract.md`
- `resources/prompt_blocks/phase/outline_pipeline/phase_05_cast_function_refinement_prompt_contract.md`
- `resources/prompt_blocks/phase/outline_pipeline/phase_06_thread_payoff_refinement_prompt_contract.md`

### Draft manifests (non-active, review lane)
- `resources/prompt_composition/manifests/proposed/outline_phase_01_chapter_spine.composition.manifest.json`
- `resources/prompt_composition/manifests/proposed/outline_phase_02_section_architecture.composition.manifest.json`
- `resources/prompt_composition/manifests/proposed/outline_phase_03_scene_draft.composition.manifest.json`
- `resources/prompt_composition/manifests/proposed/outline_phase_04_transition_causality_refinement.composition.manifest.json`
- `resources/prompt_composition/manifests/proposed/outline_phase_05_cast_function_refinement.composition.manifest.json`
- `resources/prompt_composition/manifests/proposed/outline_phase_06_thread_payoff_refinement.composition.manifest.json`

### Activation intent
- Keep these manifests non-active until review sign-off.
- Promote from `manifests/proposed/` to top-level `manifests/` only in activation PR.

## Semantically Meaningful Template Naming (Locked)
- `outline_phase_01_chapter_spine.md`
- `outline_phase_02_section_architecture.md`
- `outline_phase_03_scene_draft.md`
- `outline_phase_04_transition_causality_refinement.md`
- `outline_phase_05_cast_function_refinement.md`
- `outline_phase_06_thread_payoff_refinement.md`

Naming rules:
- Phase number + semantic intent are mandatory.
- Numeric-only segment names are forbidden in production prompt sources.
- Manifest `semantic_id` is stable identity; file paths are descriptive locators.

## Outline Pipeline V2 (Deterministic 6-Phase Flow)
Each phase is JSON-only, max 2 attempts, reason-coded fail contract on second failure.

1. `phase_01_chapter_spine`
- Prompt template: `outline_phase_01_chapter_spine.md`
- Artifact: `outline_spine_v1.json`
- Scope: chapter-only backbone.

2. `phase_02_section_architecture`
- Prompt template: `outline_phase_02_section_architecture.md`
- Artifact: `outline_sections_v1.json`
- Scope: section mini-arcs with deterministic end-condition anchors.

3. `phase_03_scene_draft`
- Prompt template: `outline_phase_03_scene_draft.md`
- Artifact: `outline_draft_v1_1.json`
- Scope: first full outline v1.1 with deterministic sequencing and required registry arrays when referenced.

4. `phase_04_transition_causality_refinement`
- Prompt template: `outline_phase_04_transition_causality_refinement.md`
- Audit artifact: `phase_04_output.json` (wrapper + report)
- Extracted handoff artifact: `outline_transitions_refined_v1_1.json` (pure outline)
- Scope: transition/causality repair and orphan elimination.

5. `phase_05_cast_function_refinement`
- Prompt template: `outline_phase_05_cast_function_refinement.md`
- Audit artifact: `phase_05_output.json` (wrapper + cast report)
- Extracted handoff artifact: `outline_cast_refined_v1_1.json` (pure outline)
- Scope: cast utility and intro/reference integrity.

6. `phase_06_thread_payoff_refinement`
- Prompt template: `outline_phase_06_thread_payoff_refinement.md`
- Artifact: `outline_final_v1_1.json`
- Scope: thread cadence and bridge alignment.

Final promote:
- `outline_final_v1_1.json` -> `outline/outline.json`
- Regenerate chapter shards and `outline/characters.json`.

## Rerun Safety Decision Table
1. Existing outline, no drafted scene outputs detected:
- `--rerun` allowed.

2. Existing outline, drafted scene outputs detected:
- hard block by default.
- allowed only with explicit `--force-rerun-with-draft`.

Drafted-scene detection signals (any one is sufficient):
- files under `draft/chapters/ch_*/scene_*.md`,
- files under `draft/chapters/ch_*/scene_*.meta.json`,
- per-scene phase artifacts under `draft/context/phase_history/ch*_sc*`,
- run pause markers tied to drafted scene phases.

`--force-rerun-with-draft` blast radius:
- invalidates draft-phase continuity assumptions for overwritten chapters/scenes,
- requires explicit warning and confirmation in logs/report.
- is enabled only when the hard flag is present; no implicit or interactive fallback.

## Prompt Template Change Specification (Plan-Only)
This section defines required prompt text changes to apply in a later implementation pass.

Global required prompt-language harmonization across all six outline pipeline phase templates:
- Include this sentence verbatim: `Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.`
- Include terminal hard-failure instructions for shared `error_v1` contract verbatim.
- Optional fields rule: if unknown/unset, omit optional fields; do not emit empty strings as placeholders.
- Registry policy sentence:
  - `characters` and `threads` are globally recommended, but become required whenever any scene references their ids.

Cross-template conflict policy to prevent validator/prompt contradiction:
- Outline-phase templates and outline-phase output-contract language must not enforce strict equality between total scenes and `expected_scene_count` by default.
- Strict equality is permitted only when exact-count mode is explicitly configured.
- Required update target: `resources/prompt_blocks/phase/output_contract/global_output_contract_rules.md` for outline-phase qualified language.

### `resources/prompt_blocks/phase/outline_pipeline/phase_01_chapter_spine_prompt_contract.md`
Required updates:
- Explicitly require `chapter_id` to be sequential integers starting at 1.
- Add explicit stability rule: chapter count should not oscillate between retries/reruns unless input constraints change.
- Clarify chapter-1 bridge normalization policy for `bridge.from_prev` (e.g., empty string policy).
- Add outline-phase guard sentence: "Timeline Lock does not apply during outlining."

### `resources/prompt_blocks/phase/outline_pipeline/phase_02_section_architecture_prompt_contract.md`
Required updates:
- Extend section schema to include required `end_condition` string per section.
- Define `end_condition` as deterministic closure target for section-final scene in phase 03.
- Require `section_id` to be sequential within each chapter.
- Add soft distribution rule: sum of `target_scene_count` should approximately align with chapter `expected_scene_count`.
- Add explicit pacing policy text: `expected_scene_count` is warning-only unless exact-count mode is explicitly configured by targets/settings.
- Add outline-phase guard sentence: "Timeline Lock does not apply during outlining."

### `resources/prompt_blocks/phase/outline_pipeline/phase_03_scene_draft_prompt_contract.md`
Required updates:
- Make scene sequencing policy explicit:
  - `scene_id` is chapter-local.
  - `scene_id` must be strictly monotonic across all scenes in chapter (including section boundaries).
- Add transition-link format policy (locked now):
  - `consumes_outcome_from` and `hands_off_to` use string reference format `"chapter_id:scene_id"` (example `"2:7"`).
  - If present in phase 03 draft, they must conform to this format and reference valid scenes.
- Remove/replace any example values that use non-locked reference format.
- Add required closure anchor for section-final scenes:
  - Each section-final scene must include `end_condition_echo` matching the phase-02 `end_condition`.
- Tighten registry requirements:
  - If any scene references character ids (`characters`, `introduces`, callbacks to character ids), top-level `characters` array is required.
  - If any scene references thread ids (`threads`, callbacks to thread ids), top-level `threads` array is required.
- Clarify that required arrays can be empty only when no scene references them.
- Add outline-phase guard sentence: "Timeline Lock does not apply during outlining."

### `resources/prompt_blocks/phase/outline_pipeline/phase_04_transition_causality_refinement_prompt_contract.md`
Required updates:
- Add deterministic section-closure requirement:
  - Preserve/repair `end_condition_echo` on section-final scenes.
- Make transition-link fields required at phase 04+:
  - `consumes_outcome_from` required on all non-first scenes.
  - `hands_off_to` required on all non-last scenes.
  - all refs must follow locked format `"chapter_id:scene_id"`.
- Require phase report to include deterministic closure and transition evidence:
  - `orphan_scene_refs_before`, `orphan_scene_refs_after`, `closure_fail_refs_after`.
- Require strict hint compliance evidence in `phase_report`:
  - `transition_hint_compliance`: array of objects `{ "hint_id": "...", "satisfied": true|false, "evidence_scene_refs": ["chapter:scene"] }`.
- Clarify evidence reference format:
  - `evidence_scene_refs` must use the same `"chapter_id:scene_id"` format.
- Clarify that extracted v1.1 outline is the phase handoff artifact.
- Add outline-phase guard sentence: "Timeline Lock does not apply during outlining."

### `resources/prompt_blocks/phase/outline_pipeline/phase_05_cast_function_refinement_prompt_contract.md`
Required updates:
- Preserve sequencing and closure anchors (`scene_id` monotonic, `end_condition_echo` intact).
- Preserve required transition-link fields and locked `"chapter_id:scene_id"` format from phase 04.
- Preserve and validate top-level registry arrays when scene references exist.
- Add outline-phase guard sentence: "Timeline Lock does not apply during outlining."

### `resources/prompt_blocks/phase/outline_pipeline/phase_06_thread_payoff_refinement_prompt_contract.md`
Required updates:
- Preserve deterministic sequencing and section closure anchors.
- Preserve required transition-link fields and locked `"chapter_id:scene_id"` format from phase 04/05.
- Require final output to maintain reference-integrity constraints for characters/threads.
- Add outline-phase guard sentence: "Timeline Lock does not apply during outlining."

### Legacy prompt surface alignment (still required)
- `resources/prompt_blocks/phase/outline/prompt_contract_and_outline_schema.md`
  - Add explicit compatibility note for chapter/scene sequencing and registry array requirements so one-pass fallback behavior does not diverge from pipeline policy.
- `resources/prompt_blocks/phase/plan/scene_card_prompt_contract_and_schema.md`
  - Add explicit consumption note for section-edge fields (including `end_condition_echo` context from outline window).

## CLI Contract Expansion (Required)
Extend `bookforge outline generate`:
- `--rerun`
- `--resume`
- `--from-phase <phase_id>`
- `--to-phase <phase_id>`
- `--phase <phase_id>`
- `--transition-hints-file <path>`
- `--strict-transition-hints`
- optional: `--force-rerun-with-draft`
- optional: `--exact-scene-count`
- optional: scene-count range input parameter (final name to be locked in CLI docs and schema)

Additional deterministic rerun rules:
- Starting from phase N requires validated artifact from phase N-1.
- If dependency missing/invalid, auto-backtrack to earliest satisfiable phase or fail with `ERROR`.
- Strict transition mode requires non-empty hints and explicit per-hint satisfaction report.
- `--resume` reuses prior successful phase artifacts and does not re-run completed valid phases.
- `--resume` cannot be used with `--new-version` in the same invocation.
- If `--resume` and `--from-phase` are both supplied, resume starts at the later of:
  - requested phase, and
  - first incomplete/invalid phase from resume metadata.
- scene-count strictness override:
  - default enforcement uses strong `expected_scene_count` validation,
  - `--exact-scene-count` forces strict exact mode where range relaxations are not allowed.

## Resume Parity Contract (Match Main `run --resume` Behavior)
Outline pipeline resume behavior must mirror key guarantees from `bookforge run --resume`:

1. Artifact reuse semantics
- Reuse only phases recorded as `success` with all required artifacts present and readable.
- If a phase artifact is missing/corrupt, that phase and all downstream phases are invalidated and re-run.

2. Phase-history backed resume
- Persist phase execution metadata per run, including status, timestamp, artifact paths, attempts.
- Resume logic must use this metadata to skip completed phases exactly as main run loop skips completed phase work.

3. Pause marker and resumable stop
- On quota/LLM pause or deterministic policy pause, write pause marker with phase + reason + context.
- Resume command reads marker and continues from correct phase without replaying successful phases.

4. Exit behavior parity
- Use explicit resumable pause exit semantics (same pause intent as main loop; non-terminal stop rather than hard failure).

5. Determinism and safety
- Resume must not silently change previously accepted phase outputs.
- Resume must preserve same output given same prior artifacts and inputs.

6. Conflict prevention
- If working outline inputs materially changed since pause (book prompt, transition hints, outline seed), resume must:
  - fail with explicit mismatch reason, or
  - require explicit override flag to discard stale phase artifacts.

7. Canonical phase artifact hierarchy
- Raw attempt: direct LLM response (`phase_0N_attempt_M.raw.json`).
- Normalized phase output: parse/normalize result (`phase_0N_output.json`).
- Handoff outline artifact: pure downstream input outline (`outline_*_v1_1.json`).
- Validation artifact: authoritative gate report (`phase_0N_validation.json`).
- No downstream phase may consume raw attempt files directly.

### Resume data and control artifacts (outline pipeline)
Required plan-level artifact set:
- `workspace/books/<book_id>/outline/pipeline_runs/<run_id>/phase_history.json`
- `workspace/books/<book_id>/outline/pipeline_runs/<run_id>/phase_0N_input.json`
- `workspace/books/<book_id>/outline/pipeline_runs/<run_id>/phase_0N_output.json`
- `workspace/books/<book_id>/outline/pipeline_runs/<run_id>/phase_0N_validation.json`
- `workspace/books/<book_id>/outline/pipeline_runs/<run_id>/phase_0N_attempt_1.raw.json`
- `workspace/books/<book_id>/outline/pipeline_runs/<run_id>/phase_0N_attempt_2.raw.json` when used
- `workspace/books/<book_id>/outline/pipeline_latest.json`
- `workspace/books/<book_id>/outline/pipeline_run_paused.json`

Pause marker minimum fields:
- `book_id`
- `run_id`
- `phase`
- `reason_code`
- `message`
- `created_at`
- `attempt`
- `resume_from_phase`
- optional `details`

## Deterministic Validation Gate Specification (Detailed)
### Sequencing gates
1. Chapter sequencing:
- `chapter_id` set must equal `[1..N]` with no gaps, duplicates, or non-integers.

2. Scene sequencing:
- For each chapter, flatten sections in order.
- `scene_id` must be strictly increasing by 1 from first to last scene in chapter.

### Reference-registry gates
1. Character registry gate:
- If any scene has non-empty `characters` or `introduces` or character-id callbacks, top-level `characters` array must exist and define all referenced ids.

2. Thread registry gate:
- If any scene has non-empty `threads` or thread-id callbacks, top-level `threads` array must exist and define all referenced ids.

### Section closure gates
1. Phase-02 closure target:
- Every section has non-empty `end_condition`.

2. Phase-03+ closure anchor:
- Section-final scene must include non-empty `end_condition_echo`.
- `end_condition_echo` must match section `end_condition` (trim-normalized; case-insensitive exact match policy).

### Transition link format and requiredness gates (Locked)
1. Reference format:
- `consumes_outcome_from` and `hands_off_to` must match regex `^[1-9][0-9]*:[1-9][0-9]*$` when populated.
- References must point to existing scenes in the current outline graph.

2. Requiredness at phase 04+:
- Non-first scene in chapter must have non-empty `consumes_outcome_from`.
- Non-last scene in chapter must have non-empty `hands_off_to`.
- Chapter-first `consumes_outcome_from` may be empty.
- Chapter-last `hands_off_to` may be empty.

3. Graph constraints:
- `consumes_outcome_from` must reference a prior scene in the same chapter within distance 1-2 unless explicit chapter-boundary carry rule is declared.
- `hands_off_to` must reference a subsequent scene in the same chapter within distance 1-2 unless explicit chapter-boundary handoff rule is declared.

4. Chapter-boundary carry policy (V2 scope):
- cross-chapter transition links in these fields are out-of-scope for V2.
- any cross-chapter reference in `consumes_outcome_from` or `hands_off_to` is a validation error.
- chapter-boundary continuity is represented through chapter bridge fields, not scene-link cross-chapter refs.

### Transition gates
- Phase-04+ cannot pass with orphan outcome refs after deterministic graph check.
- Weak handoff metrics are warning/error by threshold policy.

Weak handoff measurable definition:
- weak handoff is flagged when reciprocal link consistency fails:
  - scene A `hands_off_to` does not point to an allowed next scene, or
  - scene B lacks matching `consumes_outcome_from` back-reference within policy distance.
- severity policy:
  - warning by default,
  - error only when configured strict-handoff mode is enabled.

### Outcome concreteness gate (Measurable)
- outcome must contain:
  - at least one change verb token from configured allowlist (example families: acquire/lose/learn/commit/reveal/confront/escape/bind/unlock),
  - and at least one changed target/state axis token (item, thread, relationship, location access, custody, condition, milestone).
- outcome fails concreteness if it matches only vague/no-change patterns (example families: reflects, feels, vibes, continues, atmosphere-only) without explicit state change.
- exact token lists are validator configuration artifacts and must be reported in validation output for auditability.

### Pacing target policy gates
- default policy enforces chapter-level `expected_scene_count` strongly.
- range-target mode is supported and may validate within configured range (with high-end bias in planner selection).
- `--exact-scene-count` enforces strict exact-count matching and disables range relaxations.
- active scene-count mode must be declared in run metadata and validation output for auditability.

### Thread touch/escalation gate severity policy
- default touch target (for example `>=3`) is warning-only unless strict thread policy is configured.
- escalation-order violations are warning-only by default.
- hard fail applies only in strict thread policy mode or explicit per-project requirement.

### Warning-by-default override policy
- gates marked warning-default may be promoted to error by explicit strict CLI/config override.
- active strictness mode must be captured in run metadata and phase validation outputs.

### Fail contract
- On second failed attempt for any phase, emit standard `error_v1` JSON with `phase`, `reasons`, `validator_evidence`.

## Shared `error_v1` Contract (Required Across All Outline Phases)
Planned shared schema artifact:
- `schemas/outline_pipeline_error.schema.json`

Prompt contract requirement:
- Every outline phase prompt must define `error_v1` as the required hard-failure output shape after max attempts.
- Orchestrator and validators must emit/accept this exact structure on terminal phase failure.
- Requirement strength: this block is verbatim-required in each phase prompt template (phase 01 through phase 06).

`error_v1` minimum shape:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "phase": "phase_0N_name",
  "reasons": ["..."],
  "validator_evidence": [
    {
      "code": "validation_code",
      "message": "...",
      "path": "json.path",
      "scene_ref": "chapter:scene"
    }
  ],
  "retryable": false
}

## Prompt Compiler Activation Plan (After Review Approval)
1. Promote manifests from `resources/prompt_composition/manifests/proposed/` to `resources/prompt_composition/manifests/`.
2. Ensure allowlist contains pipeline tokens:
- `{{transition_hints}}`
- `{{outline_spine_v1}}`
- `{{outline_sections_v1}}`
- `{{outline_draft_v1_1}}`
- `{{outline_transitions_refined_v1_1}}`
- `{{outline_cast_refined_v1_1}}`
3. Update `src/bookforge/workspace.py` `PROMPT_TEMPLATE_FILES` to include six new phase templates.
4. Recompose templates and update `resources/prompt_composition/source_of_truth_checksums.json`.
5. Update prompt composition tests and outline pipeline tests together.
6. Run `book update-templates` after activation.

## Planner and Consumer Upgrades Required
### `src/bookforge/phases/plan.py`
- Extend outline window with section-edge fields and closure anchors.
- Consume transition hints and edge intent in scene-card generation.
- Preserve compatibility with older outlines missing new optional fields.

### `src/bookforge/outline.py`
- Replace one-pass flow with phase orchestrator.
- Implement dependency-aware partial reruns.
- Persist wrapper and extracted handoff artifacts for phase 04 and 05.

### `docs/help/outline_generate.md`
- Document new flags, strict-mode behavior, and phase dependency semantics.
- Document transition-hints schema location and evidence format for strict compliance mode.
- Document hard-flag behavior and blast radius for `--force-rerun-with-draft`.
- Document scene-count policy modes (default strong enforcement, range mode behavior, `--exact-scene-count` override).

### Planned hint schema artifact
- `schemas/outline_transition_hints.schema.json`
- strict mode must validate hints file against this schema before phase execution.

## Logging and Traceability (Mandatory)
Persist under:
- `workspace/books/<book_id>/outline/pipeline_runs/<run_id>/`

Per phase:
- `phase_0N_input.json`
- `phase_0N_output.json`
- `phase_0N_validation.json`
- `phase_0N_attempt_1.raw.json`
- `phase_0N_attempt_2.raw.json` when used

Special phase 04/05 handoff artifacts:
- `outline_transitions_refined_v1_1.json`
- `outline_cast_refined_v1_1.json`

Run-level:
- `outline_pipeline_report.json`
- `outline_pipeline_decisions.json`
- `outline_pipeline_latest.json`
- `phase_history.json`

Pause/resume control:
- `workspace/books/<book_id>/outline/pipeline_run_paused.json`
- include reason-coded pause metadata compatible with deterministic resume.

Prompt compiler traceability remains mandatory:
- `resources/prompt_composition/reports/compiled_trace/*.trace.json`
- `resources/prompt_composition/reports/compiled_debug/*.md`
- `resources/prompt_composition/reports/placeholder_audit/*.json`

## Risk Register (Updated)
1. Non-deterministic section closure checks.
- Mitigation: `end_condition` + `end_condition_echo` deterministic anchor policy.

2. Sequence drift causing planner/runner instability.
- Mitigation: hard gates for sequential chapter ids and monotonic chapter-local scene ids.

3. Scene references to missing top-level registries.
- Mitigation: require top-level `threads`/`characters` arrays when referenced anywhere.

4. Partial rerun undefined behavior.
- Mitigation: explicit artifact dependency graph and backtrack/fail behavior.

5. Compiler activation drift.
- Mitigation: manifests/allowlist/checksums/tests activated in one atomic change set.

6. Resume pointer/artifact drift causing incorrect phase skip.
- Mitigation: phase history integrity checks + artifact existence/hash validation before skip.

7. Resume after input mutation produces stale outputs.
- Mitigation: input fingerprint check and explicit override requirement.

## Test Plan (Expanded)
1. Sequencing and closure tests:
- Non-sequential chapter ids fail.
- Non-monotonic chapter-local scene ids fail.
- Missing section `end_condition` fails in phase 02.
- Missing or mismatched `end_condition_echo` fails in phase 03+.

2. Registry-reference tests:
- Scene references character/thread ids without top-level arrays fails.
- Scene references ids not present in arrays fails.

3. Pipeline rerun tests:
- Full rerun on existing outline succeeds.
- Phase-specific rerun enforces dependency artifacts.
- Strict transition hints mode requires evidence and fails when unsatisfied.

4. Resume parity tests:
- Pause at phase 02/04/05 and resume with no duplicate re-execution of successful prior phases.
- Missing artifact in a previously successful phase triggers deterministic invalidate-and-rerun behavior.
- Quota/reason pause writes pause marker and supports clean resume.
- Resume with changed inputs is blocked unless explicit override flag is provided.

5. Compatibility tests:
- No one-pass fallback path is exercised; outline generation routes through orchestrator path only.
- Planner and runner remain stable with activated pipeline outputs.

6. Scene-count mode tests:
- default mode enforces chapter `expected_scene_count` policy.
- range mode accepts in-range totals and applies high-end bias behavior.
- `--exact-scene-count` rejects non-exact outcomes under strict mode.

## Downstream Impact Checklist (Must Be Reviewed Per Change Set)
1. Scene-card planning impact (`src/bookforge/phases/plan.py`)
- outline window projection still provides required fields for `plan_scene`.
- new edge/link fields do not break scene-card schema generation.

2. Continuity-pack impact (`src/bookforge/phases/continuity_phase.py` and related consumers)
- chapter/scene ordering remains deterministic for continuity summary surfaces.
- thread registry consistency is preserved after outline pipeline upgrades.

3. Run-loop/cursor impact (`src/bookforge/runner.py`)
- cursor advancement assumptions remain valid with updated outline artifacts.
- chapter compile ordering remains unchanged.

4. Durable memory impact (`src/bookforge/memory/durable_state.py`)
- thread/device derivation from outline remains stable under new link/closure fields.

5. Template composition impact (`src/bookforge/prompt/composition.py`, manifests, allowlist)
- no ad hoc prompt path introduced.
- compiler checksums/placeholder audits updated in same activation change set.

## Implementation Progress Tracker (Live)
Status key: `pending`, `in_progress`, `completed`, `blocked`.

1. Plan lock + reviewer refinements consolidation: `completed`
2. CLI contract expansion (`outline generate` flags and argument plumbing): `completed`
3. Outline orchestrator implementation (6 phases + artifacts + retries): `completed`
4. Resume parity implementation for outline pipeline: `in_progress`
5. Deterministic validators (sequencing, closure, references, links, count policy): `completed`
6. Prompt template contract updates (all phase templates + output contract alignment): `completed`
7. Prompt compiler activation changes (manifests, allowlist, checksums): `completed`
8. Downstream consumer updates (`plan_scene`, continuity surfaces, runner assumptions): `in_progress`
9. Help/docs updates (`docs/help/outline_generate.md` + related): `completed`
10. Test updates and regression validation: `in_progress`

### Progress Log
- 2026-02-14 (current session): Locked implementation decisions added (no one-pass, scene-count policy, strictness override policy, hard force-rerun flag, docs requirements).
- 2026-02-14 (current session): Added CLI argument plumbing for outline pipeline flags in `src/bookforge/cli.py`.
- 2026-02-14 (current session): Added initial outline option parsing/validation scaffolding in `src/bookforge/outline.py`.
- 2026-02-14 (current session): Updated `docs/help/outline_generate.md` with new flags, constraints, and examples.
- 2026-02-14 (current session): Sanity check passed via `py_compile` for `src/bookforge/cli.py` and `src/bookforge/outline.py`.
- 2026-02-14 (current session): Replaced outline one-pass flow with 6-phase orchestrator in `src/bookforge/outline.py` with per-phase input/output/validation artifacts, wrapper+handoff split for phases 04/05, retry loop, pause marker writing, and pipeline latest/history metadata.
- 2026-02-14 (current session): Implemented deterministic validators for sequential chapter ids, monotonic chapter-local scene ids, section closure anchors (`end_condition`/`end_condition_echo`), registry-reference integrity, transition-link format/requiredness (phase 04+), and scene-count policy checks.
- 2026-02-14 (current session): Updated `tests/test_outline_generate.py` to pipeline mode (six sequential phase responses) including phase-06 JSON repair-path coverage.
- 2026-02-14 (current session): Regression subset passed: `tests/test_outline_generate.py`, `tests/test_workspace_init.py`, `tests/test_plan_scene.py`.
- 2026-02-14 (current session): Updated all six outline pipeline prompt contract blocks to align with deterministic validator gates (timeline-lock override, section end_condition anchor, link format, optional-field omission rule, error_v1 contract).
- 2026-02-14 (current session): Updated output-contract wording in `resources/prompt_blocks/phase/output_contract/global_output_contract_rules.md` to remove unconditional expected_scene_count equality and align with mode-based scene-count policy.
- 2026-02-14 (current session): Refreshed source-of-truth checksums in `resources/prompt_composition/source_of_truth_checksums.json` after prompt-block contract changes.
- 2026-02-14 (current session): Additional regression subset passed: `tests/test_prompt_composition.py`, `tests/test_prompt_render.py` (combined local subset now 14 passing tests).
- 2026-02-14 (current session): Activated six outline-phase compiler manifests from proposed to active manifests directory and updated manifest source span metadata.
- 2026-02-14 (current session): Expanded prompt token allowlist with outline pipeline tokens and `{{transition_hints}}` / `{{scene_count_policy}}`.
- 2026-02-14 (current session): Expanded workspace template distribution list to include six outline phase templates.
- 2026-02-14 (current session): Added strict transition-hints schema (`schemas/outline_transition_hints.schema.json`) and strict-mode schema validation in `src/bookforge/outline.py`.
- 2026-02-14 (current session): Extended planner outline-window payload in `src/bookforge/phases/plan.py` to include section `end_condition` plus scene edge/link fields.
- 2026-02-14 (current session): Updated planner prompt contract to consume section closure and transition-link hints.
- 2026-02-14 (current session): Refreshed composed template checksums after manifest activation; local regression subset now 16 passing tests.
- 2026-02-14 (current session): Added outline orchestrator regression tests for strict transition-hints schema validation, resume reuse semantics, dependency backtracking from `--from-phase`, and resume fingerprint mismatch protection.
- 2026-02-14 (current session): Fixed resume fingerprint drift logic and dependency-execution start index in `src/bookforge/outline.py` based on new tests.
- 2026-02-14 (current session): Local regression subset now 19 passing tests (`outline_generate`, `prompt_composition`, `prompt_render`, `workspace_init`, `plan_scene`).

### Current Blockers
- None currently blocking outline pipeline execution in this branch. Remaining work is scoped refinement (prompt contract updates + compiler activation + broader regression coverage).

## Review Package (This Pass)
Reviewer should inspect:
- this revised plan,
- orchestrator/validator implementation in `src/bookforge/outline.py`,
- CLI/help updates in `src/bookforge/cli.py` and `docs/help/outline_generate.md`,
- updated pipeline tests in `tests/test_outline_generate.py`,
- existing six outline pipeline prompt drafts and proposed manifests.

## Definition of Done
- Reviewer signs off on deterministic closure, sequencing, and registry-reference policies.
- Reviewer signs off on resume parity contract and pause/resume artifact model.
- Activation PR updates prompt templates/manifests/allowlist/checksums/tests together.
- Outline pipeline rerun and phase rerun are deterministic and dependency-safe.
- Outline pipeline `--resume` behavior is implemented and validated with parity expectations.
- Downstream planner/runner behavior remains compatible.
- One-pass outline path is not used in production path for this feature scope.
- Help docs fully describe force-rerun and scene-count policy modes.
