# Book 1 Init And Run Package

Target book:
- Title: `The Mercy Cache`
- Book ID: `veiled_ledger_b1`
- Series ID: `veiled-ledger`
- Author Ref: `eldrik-vale/v2`

Primary inputs:
- [series_brief.md](/C:/Users/Zythis/source/repos/bookforge/resources/plans/proposed/veiled_ledger_briefs/series_brief.md)
- [book_1_book_constitution_draft.md](/C:/Users/Zythis/source/repos/bookforge/resources/plans/proposed/veiled_ledger_briefs/book_1_book_constitution_draft.md)
- [book_1_outline_prompt.md](/C:/Users/Zythis/source/repos/bookforge/resources/plans/proposed/veiled_ledger_briefs/book_1_outline_prompt.md)

## Runtime Assumptions
- Use the configured Gemini 3.1 Pro stack.
- Do not override models at runtime.
- Turn-aware thinking should remain:
  - planning / T1: `high`
  - execution / T2: `low`
- Long-running commands should be launched with a timeout budget on the order of 12 hours.

## Init Command
Run this first:

```powershell
$env:PYTHONPATH='src'
python -m bookforge.cli --workspace workspace init `
  --book veiled_ledger_b1 `
  --author-ref eldrik-vale/v2 `
  --title "The Mercy Cache" `
  --genre "litrpg,progression_fantasy,dark_comedy" `
  --series-id veiled-ledger `
  --target chapters=8 `
  --target avg_scene_words=1800 `
  --target rating=pg-13_to_r `
  --target progression_density=high `
  --target combat_density=medium `
  --target mystery_density=medium
```

## Post-Init Constitution Step
After init, compare or replace the generated constitution with:
- [book_1_book_constitution_draft.md](/C:/Users/Zythis/source/repos/bookforge/resources/plans/proposed/veiled_ledger_briefs/book_1_book_constitution_draft.md)

Expected generated file:
- `workspace/books/veiled_ledger_b1/prompts/book_constitution.md`

Practical guidance:
- The init command will create a valid constitution from current defaults plus targets.
- The draft constitution file is the stronger desired target and should be used as the reference for any manual or future automated refinement.

## Outline Command
Use the saved brief as the outline prompt file:

```powershell
$env:PYTHONPATH='src'
python -m bookforge.cli --workspace workspace outline generate `
  --book veiled_ledger_b1 `
  --prompt-file resources/plans/proposed/veiled_ledger_briefs/book_1_outline_prompt.md
```

## Expected Next Workflow
After a viable outline exists:
1. Initialize the section workflow.
2. Advance sections one at a time.
3. Let each section move through `stub -> frozen -> locked`.
4. Run chapter seam finalization after each completed chapter.

Representative commands:

```powershell
$env:PYTHONPATH='src'
python -m bookforge.cli --workspace workspace workflow init --book veiled_ledger_b1
python -m bookforge.cli --workspace workspace workflow status --book veiled_ledger_b1
```

Then advance individual sections as they become available:

```powershell
$env:PYTHONPATH='src'
python -m bookforge.cli --workspace workspace workflow advance-section `
  --book veiled_ledger_b1 `
  --chapter 1 `
  --section 1
```

## What To Watch During The Run
Book 1 is the proving ground for:
- section freeze -> write -> lock reliability
- chapter seam audit / repair / finalization
- repeated overlap and restart-energy at joins
- item / inventory / custody continuity
- current-thought and thought-signature storage in the new folder structure
- clean classification of failures:
  - provider / transport
  - token / truncation
  - JSON / schema
  - prompt / repair loop weakness

## Recommended Active Progress Signals
These are the most useful current signals during a run:
- `workspace/books/veiled_ledger_b1/logs/runs/latest_run.txt`
  - current run id pointer
- `workspace/books/veiled_ledger_b1/logs/runs/run_*.progress.json`
  - active heartbeat with current phase, chapter, section, scene, repair pass, and last update time
- `workspace/books/veiled_ledger_b1/state.json`
  - current cursor and book status
- `workspace/books/veiled_ledger_b1/outline/snapshot_registry.json`
  - per-section `stub/frozen/locked` state
- `workspace/books/veiled_ledger_b1/draft/context/phase_history/...`
  - per-scene phase artifacts, lint reports, and repairs
- `workspace/logs/llm/veiled_ledger_b1/...`
  - nested transport logs by book/chapter/action
- `workspace/thoughts/current/...`
  - current-thought outputs
- `workspace/thoughts/signatures/...`
  - active signature state and ledger/index

## Live Progress Surface
The runner now writes a structured progress artifact alongside the text run log:
- `workspace/books/veiled_ledger_b1/logs/runs/<run_id>.progress.json`

Primary fields:
- `book_id`
- `run_id`
- `status`
- `phase`
- `chapter`
- `section`
- `scene`
- `repair_pass`
- `repair_pass_limit`
- `message`
- `run_log_path`
- `last_artifact_path`
- `updated_at`

Use this as the first check during long 3.1 Pro runs before digging into raw scene artifacts.
