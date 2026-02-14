# bookforge outline generate

Purpose
- Generate or regenerate the outline for a book.

Usage
- bookforge outline generate --book <id> [--rerun] [--resume] [--new-version] [--prompt-file <path>]
- bookforge outline generate --book <id> [--from-phase <phase_id> | --to-phase <phase_id> | --phase <phase_id>]
- bookforge outline generate --book <id> [--transition-hints-file <path>] [--strict-transition-hints]
- bookforge outline generate --book <id> [--scene-count-range <min:max>] [--exact-scene-count]
- bookforge outline generate --book <id> [--force-rerun-with-draft]

Scope
- Requires explicit --book (current-book selection is not implemented).

Required parameters
- --book: Book id slug.

Optional parameters
- --rerun: Regenerate an existing outline in place.
- --resume: Resume a paused outline pipeline run.
- --new-version: Create a new outline version.
- --prompt-file: Path to a plain-English outline prompt file used as grounding context (relative to the current working directory).
- --from-phase: Start from a specific outline phase id.
- --to-phase: Stop at a specific outline phase id.
- --phase: Run a single phase (same as --from-phase X --to-phase X).
- --transition-hints-file: Path to transition-hints input file.
- --strict-transition-hints: Require non-empty, schema-valid transition hints and strict compliance reporting.
- --scene-count-range: Optional scene-count range in min:max form (range mode).
- --exact-scene-count: Force strict exact matching against chapters[].pacing.expected_scene_count.
- --force-rerun-with-draft: Allow rerun even if drafted scene outputs already exist.
- --workspace: Override workspace root (global option).

Phase ids
- phase_01_chapter_spine
- phase_02_section_architecture
- phase_03_scene_draft
- phase_04_transition_causality_refinement
- phase_05_cast_function_refinement
- phase_06_thread_payoff_refinement

Compatibility and safety
- `outline generate --book <id>` remains the entrypoint.
- Outline generation runs through the 6-phase orchestrator (one-pass path is not used in this feature track).
- `--prompt-file` is treated as structured user input and rendered through composed templates.
- `--resume` cannot be combined with `--new-version`.
- `--rerun` cannot be combined with `--new-version`.
- If drafted scene outputs exist, rerun is blocked unless `--force-rerun-with-draft` is provided.
- `--phase` cannot be combined with `--from-phase` or `--to-phase`.
- Strict transition hints validates input against `schemas/outline_transition_hints.schema.json`.
- Scene-count policy:
  - Default: chapter totals are validated strongly against `expected_scene_count`.
  - Range mode: `--scene-count-range` allows in-range totals and emits high-end bias warnings.
  - Exact mode: `--exact-scene-count` enforces strict chapter-total equality.

Outputs
- Writes outline/outline.json and outline/chapters/ch_###.json.
- Outline schema v1.1 uses sections and scenes; see prompts/templates/outline.md for shape.
- If --prompt-file is provided, its content is passed as structured user guidance.
- The prompt file can include a plain-English summary, characters, world, or system notes to ground the outline.
- If the outline includes characters, writes outline/characters.json.
- Updates state.json with outline path and status when applicable.

Debugging
- If the model returns invalid JSON, the raw response is written to workspace/logs/llm/outline_generate_<timestamp>.json.
- A human-readable text copy is also written to workspace/logs/llm/outline_generate_<timestamp>.txt.
- When logging is enabled, the request prompt is written to workspace/logs/llm/outline_generate_<timestamp>.prompt.txt (system + user).
- To always log raw responses, set BOOKFORGE_LOG_LLM=1 before running.
  Example (PowerShell): $env:BOOKFORGE_LOG_LLM="1"
- If the output is truncated (MAX_TOKENS), raise BOOKFORGE_OUTLINE_MAX_TOKENS (default: 98304).
  Example (PowerShell): $env:BOOKFORGE_OUTLINE_MAX_TOKENS="98304"

- If requests time out, raise BOOKFORGE_REQUEST_TIMEOUT_SECONDS (default: 600).
  Example (PowerShell): $env:BOOKFORGE_REQUEST_TIMEOUT_SECONDS="600"

Examples
- Minimal:
  bookforge outline generate --book my_novel_v1
- Rerun outline in place:
  bookforge outline generate --book my_novel_v1 --rerun
- Resume paused outline pipeline:
  bookforge outline generate --book my_novel_v1 --resume
- With optional parameters:
  bookforge --workspace workspace outline generate --book my_novel_v1 --new-version
- With prompt file:
  bookforge --workspace workspace outline generate --book my_novel_v1 --prompt-file prompts\outline_seed.md
- Run a single phase:
  bookforge outline generate --book my_novel_v1 --phase phase_04_transition_causality_refinement --rerun
- Strict hints + exact count:
  bookforge outline generate --book my_novel_v1 --rerun --transition-hints-file prompts\transition_hints.json --strict-transition-hints --exact-scene-count
