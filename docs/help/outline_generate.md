# bookforge outline generate

Purpose
- Generate, rerun, or resume the phased outline pipeline for a book.

Usage
- bookforge outline generate --book <id> [options]

Scope
- Requires explicit --book (current-book selection is not implemented).

Required parameters
- --book: Book id slug.

Optional parameters
- --new-version: Create a new outline version.
- --prompt-file: Path to a plain-English outline prompt file used as grounding context (relative to the current working directory).
- --rerun: Run the phased outline pipeline again on an existing outline.
- --resume: Resume the latest outline pipeline run for this book.
- --from-phase / --to-phase: Restrict execution range (supports logical phases and internal step ids, including phase_04a/phase_04b).
- --phase: Alias for running one phase only.
- --transition-hints-file: Path to outline transition hints JSON.
- --strict-transition-hints: Enforce strict transition hint compliance.
- --strict-transition-bridges / --relaxed-transition-bridges: Toggle strict transition seam policy.
- --strict-location-identity / --relaxed-location-identity: Toggle strict location identity policy.
- --transition-insert-budget-per-chapter: Transition insertion routing budget.
- --allow-transition-scene-insertions / --disallow-transition-scene-insertions: Toggle insertion routing.
- --exact-scene-count: Enable exact chapter scene-count mode (strict).
- --scene-count-range MIN-MAX: Advisory chapter scene range (non-exact mode).
- --force-rerun-with-draft: Allow rerun even if drafted chapter prose already exists.
- --workspace: Override workspace root (global option).

Model and API key selection
- Outline generation resolves model from `OUTLINE_MODEL` first, then `DEFAULT_MODEL`.
- Outline generation resolves API key from `OUTLINE_API_KEY` first, then provider default (`OPENAI_API_KEY` or `GEMINI_API_KEY`).
- Planner uses `PLANNER_MODEL` / `PLANNER_API_KEY`; outline now has its own independent env knobs.

Outputs
- Writes phased pipeline artifacts under outline/pipeline_runs/<run_id>/.
- Writes outline pipeline report at outline/pipeline_runs/<run_id>/outline_pipeline_report.json.
- Updates outline/outline_pipeline_report_latest.json pointer.
- Writes outline/outline.json and outline/chapters/ch_###.json when a valid final handoff is available.
- Outline schema v1.1 uses sections and scenes; see prompts/templates/outline.md for shape.
- If --prompt-file is provided, its content is appended to the outline prompt as user guidance.
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
- With optional parameters:
  bookforge --workspace workspace outline generate --book my_novel_v1 --rerun --from-phase phase_04_transition_causality_refinement --to-phase phase_06_thread_payoff_refinement
- With prompt file:
  bookforge --workspace workspace outline generate --book my_novel_v1 --prompt-file prompts\outline_seed.md
