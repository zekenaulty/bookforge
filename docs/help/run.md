# bookforge run

Purpose
- Run the scene generation loop (plan -> preflight -> write -> repair -> state_repair -> lint -> commit).

Usage
- bookforge run --book <id> [--steps <n>] [--until chapter:N | chapter:N:scene:M] [--resume] [--ack-outline-attention-items|--ack-outline-issues]

Scope
- Requires explicit --book (current-book selection is not implemented).

Required parameters
- --book: Book id slug.

Optional parameters
- --steps: Number of loop iterations to run.
- --until: Stop condition. Formats: chapter:N or chapter:N:scene:M.
- --resume: Resume a prior run.
- --ack-outline-attention-items / --ack-outline-issues: Acknowledge non-strict outline attention items and continue writing.
- --workspace: Override workspace root (global option).


Defaults
- If neither --steps nor --until is provided, the run loop executes 1 scene step.

Outline attention gate
- Before writing, `run` checks the latest outline pipeline report at:
  - `workspace/books/<book>/outline/outline_pipeline_report_latest.json` (pointer)
  - and resolves to `workspace/books/<book>/outline/pipeline_runs/<run_id>/outline_pipeline_report.json`
- `run` blocks writing unless `overall_status` is `SUCCESS` or `SUCCESS_WITH_WARNINGS`.
- If `overall_status` is `PAUSED` or `ERROR`, writing is always blocked.
- If `overall_status=SUCCESS_WITH_WARNINGS` and `requires_user_attention=true`:
  - strict blocking (`strict_blocking=true`): run always stops before writing.
  - non-strict attention (`strict_blocking=false`): run stops unless `--ack-outline-attention-items` (or `--ack-outline-issues`) is provided.
- Ack flag semantics:
  - you are explicitly accepting non-strict outline warning risk for this run.
  - ack does not bypass `PAUSED`/`ERROR` statuses.
- Ack usage is logged in run metadata for auditability.

Resume notes
- --resume reuses phase history and scene artifacts in draft/context/phase_history to continue without re-running completed phases.

Outputs
- draft/chapters/ch_###/scene_###.md (scene prose)
- draft/chapters/ch_###.md (compiled chapter when a chapter completes)
- draft/chapters/ch_###/scene_###.meta.json (scene card + state patch + lint report)
- draft/context/continuity_pack.json
- draft/context/bible.md and draft/context/last_excerpt.md
- draft/context/phase_history/ch###_sc###/* (per-phase prompts, patches, and lint reports)
- workspace/books/<book>/logs/runs/run_<timestamp>.log
- workspace/logs/llm (when BOOKFORGE_LOG_LLM=1; includes quota error logs)


Environment
- BOOKFORGE_LINT_MODE=strict|warn|off (default: strict)
  - strict: lint + repair enforced; run stops if lint still fails.
  - warn: lint + repair attempted; failures are logged and run continues.
  - off: skip lint and repair; lint report is recorded as pass.
- Per-phase minified outline injection (default shown):
  - BOOKFORGE_PREFLIGHT_INCLUDE_OUTLINE=1
  - BOOKFORGE_WRITE_INCLUDE_OUTLINE=1
  - BOOKFORGE_STATE_REPAIR_INCLUDE_OUTLINE=1
  - BOOKFORGE_REPAIR_INCLUDE_OUTLINE=1
  - BOOKFORGE_CONTINUITY_PACK_INCLUDE_OUTLINE=0
  - BOOKFORGE_LINT_INCLUDE_OUTLINE=0
- BOOKFORGE_DURABLE_SLICE_MAX_EXPANSIONS=<int> (default: 2)
  - Max targeted durable context expansion retries per scene before strict-mode pause.

Examples
- Minimal:
  bookforge run --book my_novel_v1
- With optional parameters:
  bookforge --workspace workspace run --book my_novel_v1 --steps 10 --until chapter:3 --resume
- Continue past non-strict outline attention items:
  bookforge run --book my_novel_v1 --ack-outline-attention-items
  (alias: `--ack-outline-issues`)

- Force outline context on continuity and lint too:
  BOOKFORGE_CONTINUITY_PACK_INCLUDE_OUTLINE=1 BOOKFORGE_LINT_INCLUDE_OUTLINE=1 bookforge run --book my_novel_v1 --until chapter:1
