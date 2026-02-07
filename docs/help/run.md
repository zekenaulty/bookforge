# bookforge run

Purpose
- Run the plan/write/lint/repair loop for a book.

Usage
- bookforge run --book <id> [--steps <n>] [--until <chapter:scene>] [--resume]

Scope
- Requires book scope (explicit --book or current book).

Required parameters
- --book: Book id slug.

Optional parameters
- --steps: Number of loop iterations to run.
- --until: Stop condition, e.g. chapter:3 or chapter:3:scene:2.
- --resume: Resume a prior run.
- --workspace: Override workspace root (global option).


Defaults
- If neither --steps nor --until is provided, the run loop executes 1 scene step.

Outputs
- draft/chapters/ch_###/scene_###.md (scene prose)
- draft/chapters/ch_###.md (compiled chapter when a chapter completes)
- draft/chapters/ch_###/scene_###.meta.json (scene card + state patch + lint report)
- draft/context/continuity_pack.json
- draft/context/bible.md and draft/context/last_excerpt.md
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

Examples
- Minimal:
  bookforge run --book my_novel_v1
- With optional parameters:
  bookforge --workspace workspace run --book my_novel_v1 --steps 10 --until chapter:3 --resume

- Force outline context on continuity and lint too:
  BOOKFORGE_CONTINUITY_PACK_INCLUDE_OUTLINE=1 BOOKFORGE_LINT_INCLUDE_OUTLINE=1 bookforge run --book my_novel_v1 --until chapter:1
