# Chapter 1 Scene-by-Scene Run Analysis (criticulous_b1)

## Scope
- Command pattern: `bookforge run --book criticulous_b1 --until chapter:1:scene:N` with `--resume` after scene 1.
- No code/prompt fixes applied during execution.
- Artifacts gathered from phase history and LLM logs.

## Important Execution Caveat
`BOOKFORGE_LINT_MODE` resolved to `warn`, not `strict`.

Why:
- `.env` sets `BOOKFORGE_LINT_MODE=warn` (`.env:19`).
- Env resolution prefers `.env` over process environment (`src/bookforge/config/env.py:145-150`).
- Runner only hard-stops lint failures when lint mode is `strict` (`src/bookforge/runner.py:903-905`, `src/bookforge/runner.py:914-931`).

Impact:
- Scenes with final `lint status: fail` were still applied/persisted.

## High-Level Outcome
- Chapter 1 completed through scene 8.
- Cursor advanced to `ch002 sc001`.
- Core artifacts generated:
  - `scene_execution_summary.json`
  - `lint_issue_summary.json`
  - `llm_trace_index.json`

## Scene Execution (selected successful log per scene)
- Scene 1: `scene_001_strict_attempt3.log` -> completed (lint fail -> repair -> lint pass).
- Scene 2: `scene_002_strict_attempt3_fresh.log` -> completed (lint fail -> repair -> lint fail).
- Scene 3: `scene_003_strict.log` -> completed (lint fail -> repair -> lint fail).
- Scene 4: `scene_004_strict.log` -> completed (lint fail -> repair -> lint fail).
- Scene 5: `scene_005_strict.log` -> completed (lint fail -> repair -> lint pass).
- Scene 6: `scene_006_strict.log` -> completed (lint pass, no repair loop).
- Scene 7: `scene_007_strict.log` -> completed (lint fail -> repair -> lint fail).
- Scene 8: `scene_008_strict.log` -> completed (lint fail -> repair -> lint fail).

## Early Hard-Failure Attempts (before successful progression)
- Scene 1 attempt 1: state patch schema fail (`inventory_alignment_updates[*].remove[*]` object vs string).
- Scene 1 attempt 2: state patch schema fail (`transfer_updates[*].to` string vs object).
- Scene 2 attempt 1: paused at durable apply (`scope policy violation` on `inventory_alignment_updates`).
- Scene 2 attempt 2: immediate same pause (phase-history replay).

## Final Lint Status by Scene (phase history)
- Scene 1: pass (1 warning)
- Scene 2: fail (1 error, 5 warnings)
- Scene 3: fail (1 error, 2 warnings)
- Scene 4: fail (1 error, 2 warnings)
- Scene 5: pass (9 warnings)
- Scene 6: pass (7 warnings)
- Scene 7: fail (pipeline_state_incoherent)
- Scene 8: fail (pipeline_state_incoherent)

## Validity Assessment of Failing Lint Results
### Scene 2 (fail)
- Primary error: `milestone_repetition` for `crit_build_locked`.
- Assessment: **valid**. Pre-invariants already include `milestone: crit_build_locked = DONE`, while scene content re-finalizes build.

### Scene 3 (fail)
- Primary error: `inventory_mismatch` for office attire/button-down/loafers not in inventory/registry.
- Assessment: **policy-valid but operationally noisy**. It follows current attire/inventory policy, but highlights a modeling gap (ambient clothing not represented as canonical inventory).

### Scene 4 (fail)
- Primary error: durable continuity mismatch (`One-Hit Wonder` progress 1/10 in scene vs continuity state value 2).
- Assessment: **valid** continuity mismatch.

### Scene 7 (fail)
- LLM second-pass lint reported continuity/remove-directive errors.
- Final stored report collapsed to single `pipeline_state_incoherent` issue.
- Assessment: **valid as upstream state-invariant incoherence**, but issue-shape transformation hides the original continuity detail.

### Scene 8 (fail)
- LLM second-pass lint returned `status: pass` with warnings only.
- Final stored report became `pipeline_state_incoherent` (`Vane` HP mismatch to 100).
- Assessment: **likely invalid false positive from deterministic checker**:
  - Subject attribution is name-substring based (`src/bookforge/phases/lint_phase.py:43-54`).
  - HP regex can capture later unrelated numbers after `HP` (`src/bookforge/phases/lint_phase.py:148`).
  - Mixed-subject invariant lines like "Vane identified Artie's 1 HP ... 100% Crit Rate" are vulnerable to misattribution and wrong numeric extraction.

## LLM vs Final Lint Divergence
- Scene 8 changed from LLM `pass` to final `fail` (pipeline deterministic overlay).
- Scene 7 kept `fail` status but final issue codes diverged (`continuity` -> `pipeline_state_incoherent`).

## Routing-Plan-Relevant Signals (`lint_repair_split_routing_plan_20260213_183000.md`)
1. Many failures are state-heavy (`milestone_repetition`, `continuity`, `pipeline_state_incoherent`) -> Lane C remains heavily used.
2. `appearance_check_missing` warnings are pervasive and low signal; good candidate for lane-aware noise handling.
3. Deterministic post-lint overlays can materially alter LLM lint output; routing should log both raw LLM issues and final normalized issues.
4. Pre-lint schema/durable-apply failures occurred before lint routing could help; these need separate guardrails from lane routing.
5. In warn mode, fail-status lint can still apply state; metric collection should treat this as a separate risk axis when comparing routing lanes.

## Artifact Index
- Test run folder:
  - `workspace/books/criticulous_b1/draft/context/test_runs/ch001_scene_by_scene_20260214_032738`
- Per-scene command logs:
  - `scene_001_strict.log` ... `scene_008_strict.log` (+ retries)
- Summaries:
  - `scene_execution_summary.json`
  - `lint_issue_summary.json`
  - `llm_trace_index.json`
- Phase history:
  - `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc00X/*`
- LLM logs:
  - `workspace/logs/llm/criticulous_b1_ch001_sc00X_*`
