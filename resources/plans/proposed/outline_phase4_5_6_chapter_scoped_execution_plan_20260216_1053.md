# Outline Phase 4-6 Chapter-Scoped Execution Plan (20260216_1053)

## Purpose
Refactor outline phases 4, 5, and 6 to run chapter-by-chapter instead of full-book payloads to prevent model token exhaustion, preserve quality, and control API turn burn.

This plan is designed to keep existing phase 1-3 behavior intact while hardening phase 4-6 reliability.

## Doctrine Anchor
This plan inherits:
1. `resources/plans/proposed/outline_pipeline_doctrine_manifesto_20260216_0205.md`

Locked doctrine statement:
1. LLM authors and lints.
2. Orchestrator never authors or discards semantic content.
3. Orchestrator enforces deterministic invariants, routing, retries, and visibility.

## Why This Change Is Needed
Observed in live runs:
1. Full-book phase 4a payloads hit model completion ceilings (`finishReason=MAX_TOKENS`).
2. Even with large requested `max_tokens`, practical model behavior still truncates responses.
3. Truncated 4a output can pass partial shape checks and propagate chapter loss if guardrails are missing.
4. Re-running phases 1-3 while debugging phase 4 wastes scarce key turns.

Result:
1. We need smaller unit-of-work execution for phases 4-6.
2. We need hard invariants that prevent chapter-set loss.
3. We need phase-targeted resume/rerun to control turn budget.

## Scope
In scope:
1. Chapter-scoped execution loops for phase 4a, 4b, 5, and 6.
2. Deterministic chapter merge and chapter-set preservation gates.
3. Per-phase thinking-level policy for Gemini.
4. Resume behavior that starts at failed phase/chapter without rerunning 1-3.
5. Prompt/template contract updates for chapter-scoped payloads.
6. Tests for chapter retention, resume fidelity, and token-completion behavior.
7. Explicit chapter checkpoint contract for recoverable API failures (for example `429`) and explicit force-full-rerun controls for targeted phases.

Out of scope:
1. Phase 1-3 semantic redesign.
2. Writing-loop entity promotion redesign.
3. New downstream lint policy beyond what is required for chapter retention and phase handoff integrity.

## High-Level Design
Phases 1-3 remain full-book.

Phases 4-6 become chapter-scoped loops:
1. Determine stable chapter ID sequence from phase 3 handoff artifact.
2. For each chapter in sequence:
3. Build chapter-scoped prompt payload.
4. Execute phase step for that chapter.
5. Validate chapter output.
6. Merge chapter back into working full-outline object.
7. Run deterministic invariants after each merge.

At phase end:
1. Persist merged full-outline handoff artifact.
2. Persist chapter-level reports and aggregated phase report.

## Phase-by-Phase Chapter Contracts
### Phase 4a (transition seam analysis)
Input:
1. Chapter N outline slice.
2. Optional chapter N-1 / N+1 bridge context summary (read-only).
3. Transition hints filtered to chapter N.
4. Phase policy payload (strict bridges, insertion budget, exact-count mode).

Output:
1. Chapter N seam analysis report only.
2. Candidate seams for chapter N only.
3. No requirement to echo entire book.

### Phase 4b (transition execution)
Input:
1. Original chapter N slice.
2. Selected seam candidates for chapter N from 4a.
3. Chapter policy context (budget/exact mode/strictness).

Output:
1. Refined chapter N with transition fields updated.
2. Inserted transition scenes authored by LLM when requested.
3. Chapter execution report.

Hard rule:
1. If insertion is required and chapter output does not include it, fail and retry.
2. Never synthesize inserted scenes in code.

### Phase 5 (cast function refinement)
Input:
1. Chapter N slice from phase 4 output.
2. Read-only global character ledger summary.

Output:
1. Refined chapter N slice.
2. Chapter cast report.

### Phase 6 (thread/payoff refinement)
Input:
1. Chapter N slice from phase 5 output.
2. Read-only global thread ledger summary.
3. Neighbor bridge context where needed (prev/next chapter bridge lines).

Output:
1. Refined chapter N slice.
2. Chapter thread/payoff report.

## Deterministic Invariants (Hard Gates)
These checks run after every chapter merge in phases 4-6:
1. Chapter count unchanged versus phase 3 baseline.
2. Chapter ID set unchanged versus phase 3 baseline.
3. Chapter ordering unchanged.
4. Non-target chapters unchanged (hash/structural equality after canonical normalization).
5. Required scene linkage and transition contract still valid for target chapter.
6. No placeholder identity tokens in required transition fields where policy forbids them.

Failure handling:
1. On chapter invariant failure: fail chapter attempt and retry with targeted fix list.
2. On retry exhaustion: fail phase with reason-coded error and stop.
3. Never drop or auto-heal chapters in orchestrator.

## Thinking-Level Policy (Gemini)
Goal:
1. Constrain reasoning overhead to prevent completion truncation while retaining quality where needed.

Policy defaults:
1. Phase 4a: `high`
2. Phase 4b: `high`
3. Phase 5: `high`
4. Phase 6: `high`

Env override hierarchy:
1. `OUTLINE_PHASE_04A_THINKING_LEVEL`
2. `OUTLINE_PHASE_04B_THINKING_LEVEL`
3. `OUTLINE_PHASE_05_THINKING_LEVEL`
4. `OUTLINE_PHASE_06_THINKING_LEVEL`
5. `OUTLINE_THINKING_LEVEL`
6. `GEMINI_THINKING_LEVEL`
7. Phase fallback default

Notes:
1. Do not send legacy `thinking_budget` with `thinkingLevel`.
2. Keep request logging explicit for effective thinking level per attempt.

## Resume and Turn-Budget Behavior
Required behavior:
1. `--resume --from-phase X --to-phase X` must only execute requested phase steps.
2. If phase 3 is already successful, phase 4 debug loops must never re-run phases 1-3.
3. Resume pointer must be explicit and auditable in artifacts.
4. Phase history must include per-chapter progress for chapter-scoped phases.
5. Default resume behavior for chapter-scoped phases must skip chapters already marked `success`.
6. Recoverable failures (including `429`) must pause at chapter granularity and preserve successful prior chapter outputs.
7. Resume after a recoverable failure must restart at the first non-success chapter for the active phase (for example: fail on chapter 2 -> resume begins at chapter 2).
8. Full rerun for a selected phase range must be explicitly opt-in and must not happen implicitly during resume.

Phase history extension:
1. For phases 4-6, store `chapter_attempts` map:
2. `chapter_id -> {status, attempts, validation_summary}`
3. Store `resume_cursor`:
4. `{phase_id, next_chapter_id, reason_code, updated_at}`
5. Store `phase_run_mode`:
6. `resume_incremental | force_full_rerun`

CLI/behavior contract:
1. Incremental mode (default for resume): `--resume --from-phase phase_04a --to-phase phase_04a`
2. Force full rerun mode (targeted phases only): add `--force-phase-full-rerun` (new flag) to ignore chapter success checkpoints for the selected phase range while still honoring `--from-phase/--to-phase`.
3. If `--force-phase-full-rerun` is absent, previously successful chapters in selected phases are never re-executed.
4. If `--force-phase-full-rerun` is present, chapter-scoped phases in selected range always restart from chapter 1.

## Artifacts
For each chapter-scoped phase:
1. `phase_<id>_chapter_<NNN>_input.json`
2. `phase_<id>_chapter_<NNN>_attempt_raw_<k>.json`
3. `phase_<id>_chapter_<NNN>_output.json`
4. `phase_<id>_chapter_<NNN>_validation.json`

Aggregated per-phase:
1. `phase_<id>_merged_output.json`
2. `phase_<id>_summary.json`
3. `phase_<id>_checkpoint.json` (chapter statuses + resume cursor + run mode)

Handoffs:
1. Phase 4 -> `outline_transitions_refined_v1_1.json`
2. Phase 5 -> `outline_cast_refined_v1_1.json`
3. Phase 6 -> `outline_final_v1_1.json`

## Prompt and Template Changes
Templates to refactor for chapter scope:
1. `resources/prompt_templates/outline_phase_04a_transition_seam_analysis.md`
2. `resources/prompt_templates/outline_phase_04b_transition_execution.md`
3. `resources/prompt_templates/outline_phase_05_cast_function_refinement.md`
4. `resources/prompt_templates/outline_phase_06_thread_payoff_refinement.md`

Contract changes:
1. Inputs are chapter slice + required context summaries, not full outline.
2. Outputs must be chapter slice or chapter report per phase contract.
3. Explicit "do not echo full book" instruction.
4. Explicit "return JSON only" instruction remains mandatory.

## File-by-File Touchpoints
Core orchestration:
1. `src/bookforge/outline.py`
2. `src/bookforge/phases/outline/context.py`
3. `src/bookforge/phases/outline/artifacts.py`
4. `src/bookforge/phases/outline/validators.py`

Phase handlers:
1. `src/bookforge/phases/outline/phase_04a_transition_seam_analysis.py`
2. `src/bookforge/phases/outline/phase_04b_transition_execution.py`
3. `src/bookforge/phases/outline/phase_05_cast_function_refinement.py`
4. `src/bookforge/phases/outline/phase_06_thread_payoff_refinement.py`

LLM client and config:
1. `src/bookforge/llm/gemini_client.py`
2. `src/bookforge/llm/client.py`
3. `src/bookforge/config/env.py` (if adding phase-specific thinking env docs/reads there later)

Docs/help:
1. `docs/help/outline_generate.md`
2. `docs/help/run.md` (if gate semantics need mention)

## Validation and Failure Policy Updates
Add hard validator checks for:
1. chapter-set preservation (required in phases 4-6).
2. non-target chapter immutability in chapter-scoped merges.
3. required insertion realization in 4b when selected.
4. checkpoint integrity (no chapter marked success without output + validation artifacts).

On failures:
1. Retry with targeted, chapter-scoped fix list.
2. Do not escalate with full-book retry payload.
3. Emit reason codes:
4. `chapter_set_mismatch`
5. `non_target_chapter_mutation`
6. `required_insertion_unresolved`
7. `phase_output_truncated_or_invalid_json`
8. `rate_limited_retry_exhausted`
9. `resume_cursor_missing_or_invalid`
10. `phase_force_full_rerun_requested`

## Test Plan
Unit tests:
1. Chapter slicing returns stable target and non-target partitions.
2. Chapter merge preserves non-target chapters exactly.
3. Chapter set mismatch detection hard-fails.
4. Phase-level thinking configuration resolution precedence.

Integration tests:
1. Resume phase 4 only from successful phase 3 run.
2. Full phase 4 chapter-loop success without chapter loss.
3. Phase 5 chapter-loop success with chapter retention.
4. Phase 6 chapter-loop success with chapter retention.
5. Regression test: no 1-3 rerun when phase-targeted resume is requested.
6. Recovery test: simulated `429` on chapter 2 sets checkpoint cursor to chapter 2 and exits paused.
7. Resume test: rerun with `--resume` starts at chapter 2 and does not re-run chapter 1.
8. Force rerun test: `--force-phase-full-rerun --from-phase phase_04a --to-phase phase_06` reruns all chapters in 4a/4b/5/6 regardless of prior success.

Runtime audit checks:
1. Each chapter in 4-6 has explicit attempt artifacts.
2. Effective `thinkingLevel` present in request logs.
3. `finishReason` trend improves (`STOP` expected in most chapter calls).

## Rollout Sequence
1. Implement chapter-loop infrastructure and invariants in orchestrator/helpers.
2. Refactor phase 4a/4b prompts and handlers to chapter scope.
3. Validate phase 4 only on existing run using resume.
4. Refactor phase 5 prompt/handler to chapter scope.
5. Validate phase 5 only using resume.
6. Refactor phase 6 prompt/handler to chapter scope.
7. Validate phase 6 only using resume.
8. Add checkpoint cursor + force-full-rerun mode and validate both incremental and forced execution paths.
9. Run full end-to-end once after all phase-target tests pass.

## Acceptance Criteria
1. Phases 4-6 execute chapter-scoped and persist merged full-outline handoffs.
2. No chapter drop can pass validation.
3. Phase-target resume does not re-run phases 1-3.
4. Phase 4 no longer fails from full-book truncation in normal operation.
5. Logs show explicit phase-specific thinking level and stable completion behavior.
6. Pipeline report remains deterministic and auditable.
7. On chapter-level `429`, pipeline pauses with a persisted resume cursor at the failing chapter.
8. Incremental resume reuses successful chapter outputs and restarts exactly at the first non-success chapter.
9. `--force-phase-full-rerun` fully re-executes selected chapter-scoped phases and is always explicit in artifacts/reporting.

## Risks and Mitigations
Risk:
1. Chapter-scoped prompts may lose cross-chapter context quality.
Mitigation:
2. Include bounded bridge/thread ledger context summaries.

Risk:
1. Merge logic bugs could mutate non-target chapters.
Mitigation:
2. Hash-based and structural post-merge invariants.

Risk:
1. Increased artifact volume.
Mitigation:
2. Structured naming and summarized report rollups.

## Open Decisions
1. Whether phase 6 should include both previous and next chapter summaries by default or only previous.
2. Whether phase 4b should allow multi-scene insertion per seam in first rollout, or only one inserted scene per seam.
3. Whether phase-specific thinking defaults should also be exposed as CLI flags or remain env-only.
