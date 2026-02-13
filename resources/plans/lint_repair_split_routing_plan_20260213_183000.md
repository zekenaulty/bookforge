# Lint/Repair Split Routing Plan (20260213_183000)

## Purpose
Reduce lint/repair latency and token burn while preserving continuity correctness by splitting failure handling into explicit lanes (prose-only vs state-heavy), with deterministic routing and strict safety guards.

## Clarifying Decision on Current Flow
- Current behavior runs `state_repair` before lint. We keep that baseline in phase 1.
- We are adding **routing**, not removing safeguards blindly.
- Conceptually yes: this introduces a deterministic triage layer (a form of state/prose issue routing) and optionally specialized lint lanes.
- We only skip expensive paths when issue class and contracts prove it is safe.

## Why This Is Needed (Receipts)
- Scene windows in recent `ch001` run cluster around 23-24 minutes for retry-heavy scenes.
- Prompt payloads are largest in `state_repair` and `repair_scene`:
  - `state_repair` avg ~83 KB prompts, max ~100 KB.
  - `repair_scene` avg ~78 KB prompts.
  - `write_scene` avg ~75 KB prompts.
- Many fail passes include prose-heavy issues (`pov_drift`) that do not require full state mutation.

## Scope
- In scope:
  - Deterministic issue classification and routing.
  - Optional prose-only repair lane.
  - Optional lane-specific lint prompts/models.
  - Retry policy tuning per lane.
- Out of scope:
  - Removing continuity/state safety checks.
  - Parallel prose mutation without merge ownership.

## Lanes (Target Architecture)
### Lane A: Prose-Only Fast Path
For issues that should not mutate durable state.

Candidate issue codes:
- `pov_drift`
- `prose_internal_id`
- naming/style-only issues that do not imply custody/mechanics changes

Behavior:
- Run compact `repair_prose_only` prompt with minimal context.
- Prose edits only.
- Keep patch unchanged except allowed metadata fields (or return no patch delta).
- Re-lint.
- If still failing or new state issues appear, escalate to Lane C.

### Lane B: Deterministic-Only / Gate Checks
For checks already deterministic in code.

Examples:
- UI gate violations
- internal id prose hygiene
- simple invariant contradiction detectors

Behavior:
- Run deterministic checks first.
- If deterministic-only fix is possible via tiny prose transform, route to Lane A.
- Otherwise proceed to LLM lint.

### Lane C: Full State + Prose Repair
For continuity/state/custody/mechanics conflicts.

Examples:
- `pipeline_state_incoherent`
- durable constraints / custody conflicts
- stat ownership mismatches requiring patch/state mutation

Behavior:
- Existing full cycle remains: repair -> state_repair -> lint.

## Phased Rollout
### Story 1: Routing Classifier (No Behavioral Risk)
- Add deterministic classifier that maps issues to lane eligibility.
- Log route decisions per scene (reason + issue codes).
- No behavior changes yet (observe-only mode).

Touchpoints:
- `src/bookforge/runner.py`
- possibly `src/bookforge/pipeline/lint/helpers.py`

Acceptance:
- Route decision logs are created for every lint fail.
- No run behavior changes in observe-only mode.

### Story 2: Prose-Only Repair Lane (Guarded)
- Add a new repair prompt template for prose-only edits (compact input).
- Add phase function for prose-only repair.
- Route only when all issues are lane-safe and no state-impact codes are present.

Touchpoints:
- New template: `resources/prompt_templates/repair_prose_only.md`
- New phase module: `src/bookforge/phases/repair_prose_only_phase.py`
- Runner routing changes in `src/bookforge/runner.py`

Acceptance:
- Prose-only fails avoid `state_repair` call when safe.
- Scene output remains schema-valid and lint-correct.

### Story 3: Lane-Specific Lint Prompting / Model Assignment
- Split lint prompt into shared core + optional lane overlays.
- Add lane-specific model selection (using existing per-phase seams first; optional task-level extension later).
- Keep one lint_report schema and one final aggregation path.

Touchpoints:
- `resources/prompt_templates/lint.md`
- optional additional lint lane template fragments
- `src/bookforge/phases/lint_phase.py`
- `src/bookforge/llm/factory.py` (if new phase keys introduced)

Acceptance:
- Lane-specific linting reduces average prompt size for prose-only paths.
- No change in lint report contract.

### Story 4: Escalation, Retries, and Safety Rails
- Add strict escalation rules:
  - Lane A failure => Lane C fallback.
  - Any introduced state-coded issue => Lane C.
- Lane-specific retry budgets and timeouts.
- Preserve strict-mode behavior semantics.

Acceptance:
- No dead-end loops.
- Fallback path always available.

### Story 5: Measurement and Decision Gate
- Add per-scene metrics:
  - lane used
  - lint/repair/state_repair call counts
  - total duration
  - token estimate proxies (prompt size)
- Compare against baseline chapter run.

Acceptance:
- Measurable reduction in average scene duration and high-cost phase invocations.
- No increase in invalid pass rate or continuity regressions.

## Routing Policy (Initial)
Use Lane A only when all are true:
- All failing issues are in prose-safe allowlist.
- No issue code indicating durable/state inconsistency.
- No deterministic evidence of custody/state mismatch.
- Current patch does not include required unresolved state mutations.

Otherwise route Lane C.

## Risk Register
- Risk: Misclassification sends state issue down prose-only path.
  - Mitigation: conservative allowlist + immediate escalation to Lane C.
- Risk: Split prompts drift from shared contracts.
  - Mitigation: shared core blocks + contract tests.
- Risk: Added complexity creates debugging overhead.
  - Mitigation: explicit route logs and per-scene lane metadata.
- Risk: Parallel execution introduces merge conflicts.
  - Mitigation: do not parallelize prose mutations in first rollout.

## Edge Cases
- Mixed fail bundle (e.g., `pov_drift` + `pipeline_state_incoherent`).
- Lint false positives that move lanes repeatedly.
- Strict mode scenes where warnings become errors due to mode.
- Scene transitions with scope overrides where prose and state are both touched.
- Repair introducing new state-bearing UI/mechanics unexpectedly.

## Definition of Done
- Routing exists with deterministic, auditable decisions.
- Prose-only failures can be repaired without invoking full state_repair path when safe.
- Full state lane remains authoritative and unchanged for state-heavy failures.
- Run logs include lane/route metrics per scene.
- Baseline vs new run comparison demonstrates meaningful latency/cost reduction without correctness regressions.

## Status Tracker
- Story 1: `pending`
- Story 2: `pending`
- Story 3: `pending`
- Story 4: `pending`
- Story 5: `pending`
