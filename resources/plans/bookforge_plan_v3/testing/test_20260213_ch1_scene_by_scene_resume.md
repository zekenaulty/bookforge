# Test Run Log: criticulous_b1 chapter 1 scene-by-scene resume (2026-02-13)

## Objective
- Generate full chapter 1 (`sc001`..`sc008`) using incremental `--until chapter:1:scene:N` targets.
- Use `--resume` for scenes 2..8.
- Capture failures for post-run fix batching.

## Environment
- Repo: `C:\Users\Zythis\source\repos\bookforge`
- Command binary: `.\.venv\Scripts\bookforge.exe`
- Workspace: `workspace`
- Book: `criticulous_b1`

## Commands Executed
1. `.\.venv\Scripts\bookforge.exe --workspace workspace run --book criticulous_b1 --until chapter:1:scene:1`
2. `.\.venv\Scripts\bookforge.exe --workspace workspace run --book criticulous_b1 --until chapter:1:scene:2 --resume`
3. `.\.venv\Scripts\bookforge.exe --workspace workspace run --book criticulous_b1 --until chapter:1:scene:3 --resume`
4. `.\.venv\Scripts\bookforge.exe --workspace workspace run --book criticulous_b1 --until chapter:1:scene:4 --resume`
5. `.\.venv\Scripts\bookforge.exe --workspace workspace run --book criticulous_b1 --until chapter:1:scene:5 --resume`
6. `.\.venv\Scripts\bookforge.exe --workspace workspace run --book criticulous_b1 --until chapter:1:scene:6 --resume`
7. `.\.venv\Scripts\bookforge.exe --workspace workspace run --book criticulous_b1 --until chapter:1:scene:7 --resume`
8. `.\.venv\Scripts\bookforge.exe --workspace workspace run --book criticulous_b1 --until chapter:1:scene:8 --resume`

## Runtime Notes
- No shell-level timeout after increasing command timeout to 2 hours.
- Scene duration range observed: ~7 min to ~24 min.
- Chapter compiled at scene 8; cursor advanced to `ch002 sc001`.

## Scene Outcome Matrix
- `ch001_sc001`: `lint=fail`, committed (soft mode). Issue: `pipeline_state_incoherent` (wallet custody contradiction between `must_stay_true` and `character_states.invariants`).
- `ch001_sc002`: `lint=pass` (warnings only). Warnings include `appearance_check_missing`, `stat_unowned`.
- `ch001_sc003`: `lint=fail`, committed (soft mode). Primary error: `pov_drift` (`me` in narration).
- `ch001_sc004`: `lint=pass` (warnings only). Includes `constraint_violation`, `stat_mismatch`, `stat_unowned`, `appearance_check_missing`.
- `ch001_sc005`: `lint=fail`, committed (soft mode). Primary error: `pov_drift` (`me` in narration).
- `ch001_sc006`: `lint=pass` (warnings only). Includes `word_count_deviation`, `item_naming_descriptor`, `stat_unowned`, `appearance_check_missing`.
- `ch001_sc007`: first lint fail, second lint pass after repair cycle; committed.
- `ch001_sc008`: `lint=fail`, committed (soft mode). Issue: `pipeline_state_incoherent` for `CHAR_VANE` item posture contradiction (`invariants` vs inventory/containers).

## High-Value Findings
1. `pipeline_state_incoherent` still appears at chapter boundaries of state posture changes (`sc001`, `sc008`), indicating stale or contradictory invariant lines remain in character state.
2. `pov_drift` false-positive/true-positive sensitivity remains high in narration where writer voice slips pronouns into close-third sentences.
3. `appearance_check_missing` persists as warnings in multiple scenes; not blocking but noisy.
4. Resume workflow is stable for scene-by-scene progression; no phase-history corruption observed.

## Artifacts to Review Next
- `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc001/lint_report.json`
- `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc003/lint_report.json`
- `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc005/lint_report.json`
- `workspace/books/criticulous_b1/draft/context/phase_history/ch001_sc008/lint_report.json`
- Run logs:
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_075056.log`
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_080621.log`
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_082609.log`
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_085104.log`
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_090406.log`
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_092801.log`
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_093518.log`
  - `workspace/books/criticulous_b1/logs/runs/run_20260213_095857.log`

## Suggested Next Fix Batch (no changes applied in this run)
1. Harden invariant reconciliation for character state in scenes that include custody transitions (target incoherence on `sc001/sc008`).
2. Tune `pov_drift` handling in prompt/heuristic to avoid close-third sentence false catches while preserving true first-person detection.
3. Decide whether `appearance_check_missing` remains advisory warning or should be repaired by default in write/state_repair.
