# bookforge run

Purpose
- Run the scene generation loop (plan -> preflight -> continuity -> write -> state_repair -> lint -> repair loop -> apply/commit).
- This is the lower-level writer loop.
- `run` now acts as a macro over the extracted scene-phase execution actions rather than owning a separate per-scene implementation.
- In the section workflow model, `run` is typically invoked indirectly by `bookforge workflow write-section`, `bookforge workflow advance-section`, or `bookforge workflow resume-paused-section` after a section has been frozen.
- Those section-level commands now use a dedicated section-range macro over the same lower-level scene-phase actions rather than calling `run` as their only macro entry point.
- For the first extracted scene-phase surface, prefer:
  - `bookforge workflow plan-scene`
  - `bookforge workflow preflight-scene-state`
  - `bookforge workflow generate-continuity-pack`
  - `bookforge workflow scene-readiness`
  - `bookforge workflow write-scene-prose`
  - `bookforge workflow state-repair-scene-patch`
  - `bookforge workflow lint-scene-prose`
  - `bookforge workflow repair-scene-prose`
  - `bookforge workflow apply-scene-commit`
- Runtime family: `section_write`.

Usage
- bookforge run --book <id> [--steps <n>] [--until chapter:N | chapter:N:scene:M] [--resume] [--ack-outline-attention-items] [--force-outline-gate-bypass]

Scope
- Requires explicit --book (current-book selection is not implemented).

Required parameters
- --book: Book id slug.

Optional parameters
- --steps: Number of loop iterations to run.
- --until: Stop condition. Formats: chapter:N or chapter:N:scene:M.
- --resume: Resume a prior run.
- --ack-outline-attention-items (alias: --ack-outline-issues): Acknowledge non-blocking outline attention items so writing can proceed.
- --force-outline-gate-bypass: Bypass outline write gate checks (testing/debug only).
- --workspace: Override workspace root (global option).


Defaults
- If neither --steps nor --until is provided, the run loop executes 1 scene step.

Resume notes
- --resume reuses phase history and scene artifacts in draft/context/phase_history to continue without re-running completed phases.
- When a scene-phase action pauses, `run` converts that pause back into the legacy `draft/context/run_paused.json` surface so scoped resume and workspace observation continue to work.

Outline write gate
- `bookforge run` checks the latest outline pipeline report before writing.
- Writing is blocked when outline status is `ERROR` or `PAUSED`.
- Writing is blocked when strict attention items are present unless `--force-outline-gate-bypass` is set.
- Non-strict attention items require explicit acknowledgement via `--ack-outline-attention-items`.
- `--force-outline-gate-bypass` is intended for controlled testing only.
- In the transitional section workflow implementation, `--force-outline-gate-bypass` may still be needed when writing against workflow-frozen sections derived from older non-success outline runs.

Lineage note
- `run` consumes the currently materialized section/scene scope. It does not choose deep-outline lineage on its own.
- If you need to establish or repair outline lineage, do that through `bookforge workflow ...` or `bookforge outline generate`, not by treating `run` as an outline-resume surface.

Outputs
- draft/chapters/ch_###/scene_###.md (scene prose)
- draft/chapters/ch_###.md (compiled chapter output; may be provisional when only some chapter sections are locked)
- draft/chapters/ch_###/scene_###.meta.json (scene card + state patch + lint report)
- draft/context/continuity_pack.json
- draft/context/bible.md and draft/context/last_excerpt.md
- draft/context/phase_history/ch###_sc###/* (per-phase prompts, patches, and lint reports)
- workspace/books/<book>/logs/runs/run_<timestamp>.log
- workspace/logs/llm (when BOOKFORGE_LOG_LLM=1; includes quota error logs)

Supervised result surface
- When the supervision surface is active, `run` emits a main-branch execution result with:
  - the public outcome status
  - `pre_reconciliation_status`
  - `state_change_status`
  - `canonical_change_status`
  - `integrity_change`
  - `pre_revision_id`
  - `post_revision_id`
- This makes quota pauses, clean exits, and integrity-degraded outcomes observable without reconstructing them from raw logs.


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

- Force outline context on continuity and lint too:
  BOOKFORGE_CONTINUITY_PACK_INCLUDE_OUTLINE=1 BOOKFORGE_LINT_INCLUDE_OUTLINE=1 bookforge run --book my_novel_v1 --until chapter:1

Related commands
- `bookforge workflow init`
- `bookforge workflow freeze-section`
- `bookforge workflow plan-scene`
- `bookforge workflow preflight-scene-state`
- `bookforge workflow generate-continuity-pack`
- `bookforge workflow scene-readiness`
- `bookforge workflow write-scene-prose`
- `bookforge workflow state-repair-scene-patch`
- `bookforge workflow lint-scene-prose`
- `bookforge workflow repair-scene-prose`
- `bookforge workflow apply-scene-commit`
- `bookforge workflow write-section`
- `bookforge workflow advance-section`
- `bookforge workflow resume-paused-section`

Branch-scoped writer note
- `bookforge workflow scene-readiness`, scene-phase commands, and `bookforge workflow write-section` accept `--branch-id <id>` when the caller wants to execute against a derived branch snapshot instead of canonical `main`.
- `bookforge run` remains the batch/operator macro over `main`; branch-local authoring should use the workflow scene/section surfaces.
