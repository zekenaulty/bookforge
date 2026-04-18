# bookforge outline generate

Purpose
- Generate, rerun, or resume the phased outline pipeline for a book.
- This remains the lower-level batch outline surface.
- For the new iterative section lifecycle, prefer `bookforge workflow` and use `outline generate` to produce or refresh source outline artifacts.

Usage
- `bookforge outline generate --book <id> [options]`

Scope
- Requires explicit `--book` (current-book selection is not implemented).

Required parameters
- `--book`: Book id slug.

Optional parameters
- `--new-version`: Create a new outline version.
- `--prompt-file`: Path to a plain-English outline prompt file used as grounding context (relative to current working directory).
- `--rerun`: Run the phased outline pipeline again on an existing outline.
- `--resume`: Resume the latest outline pipeline run for this book.
- `--force-phase-full-rerun`: In chapter-scoped phases (4a/4b/5/6), rerun all chapters in selected phase range instead of reusing successful chapter checkpoints.
- `--from-phase` / `--to-phase`: Restrict execution range (supports logical phases and internal step ids, including `phase_04a`/`phase_04b`).
- `--phase`: Alias for running one phase only.
- `--transition-hints-file`: Path to outline transition hints JSON.
- `--strict-transition-hints`: Enforce strict transition hint compliance.
- `--strict-transition-bridges` / `--relaxed-transition-bridges`: Toggle strict transition seam policy.
- `--strict-location-identity` / `--relaxed-location-identity`: Toggle strict location identity policy.
- `--transition-insert-budget-per-chapter`: Transition insertion routing budget.
- `--allow-transition-scene-insertions` / `--disallow-transition-scene-insertions`: Toggle insertion routing.
- `--exact-scene-count`: Enable exact chapter scene-count mode (strict).
- `--scene-count-range MIN-MAX`: Advisory chapter scene range (non-exact mode).
- `--force-rerun-with-draft`: Allow rerun even if drafted chapter prose already exists.
- `--workspace`: Override workspace root (global option).

Model and API key selection
- Outline generation resolves model from `OUTLINE_MODEL` first, then `DEFAULT_MODEL`.
- Outline generation resolves API key from `OUTLINE_API_KEY` first, then provider default (`OPENAI_API_KEY` or `GEMINI_API_KEY`).
- Planner uses `PLANNER_MODEL` / `PLANNER_API_KEY`; outline now has its own independent env knobs.

Thinking level controls (Gemini)
- Shared fallbacks:
  - `OUTLINE_THINKING_LEVEL`
  - `GEMINI_THINKING_LEVEL`
- Per-logical-phase overrides:
  - `OUTLINE_PHASE_01_THINKING_LEVEL`
  - `OUTLINE_PHASE_02_THINKING_LEVEL`
  - `OUTLINE_PHASE_03_THINKING_LEVEL`
  - `OUTLINE_PHASE_04_THINKING_LEVEL`
  - `OUTLINE_PHASE_05_THINKING_LEVEL`
  - `OUTLINE_PHASE_06_THINKING_LEVEL`
- Per-step overrides (highest priority for chapter-scoped splits):
  - `OUTLINE_PHASE_04A_THINKING_LEVEL`
  - `OUTLINE_PHASE_04B_THINKING_LEVEL`
  - `OUTLINE_PHASE_05_THINKING_LEVEL`
  - `OUTLINE_PHASE_06_THINKING_LEVEL`
- Valid values: `minimal`, `low`, `medium`, `high`.
- Resolution precedence:
  - step-specific key -> logical phase key -> `OUTLINE_THINKING_LEVEL` -> `GEMINI_THINKING_LEVEL` -> internal defaults.

Outputs
- Writes phased pipeline artifacts under outline/pipeline_runs/<run_id>/.
- Writes outline pipeline report at outline/pipeline_runs/<run_id>/outline_pipeline_report.json.
- Updates outline/outline_pipeline_report_latest.json pointer.
- For chapter-scoped phases 4a/4b/5/6, writes chapter artifacts:
  - phase_<id>_chapter_<NNN>_input.json
  - phase_<id>_chapter_<NNN>_attempt_raw_<k>.json
  - phase_<id>_chapter_<NNN>_output.json
  - phase_<id>_chapter_<NNN>_validation.json
  - <step_id>_checkpoint.json (chapter attempts + resume cursor)
- Writes outline/outline.json and outline/chapters/ch_###.json when a valid final handoff is available.
- Outline schema v1.1 uses sections and scenes; see prompts/templates/outline.md for shape.
- If --prompt-file is provided, its content is appended to the outline prompt as user guidance.
- The prompt file can include a plain-English summary, characters, world, or system notes to ground the outline.
- If the outline includes characters, writes outline/characters.json.
- Updates state.json with outline path and status when applicable.
- In the section workflow model, these run artifacts are the source material used to initialize/freeze sections into canonical `outline/outline.json`.

Debugging
- If the model returns invalid JSON, raw request/response logs are written under `workspace/logs/llm/` using phase/attempt labels.
- When logging is enabled, prompt copies are written as `.prompt.txt`.
- To always log raw responses, set `BOOKFORGE_LOG_LLM=1`.
  - Example (PowerShell): `$env:BOOKFORGE_LOG_LLM="1"`
- If output is truncated (`MAX_TOKENS`), raise `BOOKFORGE_OUTLINE_MAX_TOKENS` (current default: `58982400`).
  - Example (PowerShell): `$env:BOOKFORGE_OUTLINE_MAX_TOKENS="60000000"`
- If requests time out, raise `BOOKFORGE_REQUEST_TIMEOUT_SECONDS` (default: `600`).
  - Example (PowerShell): `$env:BOOKFORGE_REQUEST_TIMEOUT_SECONDS="600"`

Examples
- Minimal:
  - `bookforge outline generate --book my_novel_v1`
- With optional parameters:
  - `bookforge --workspace workspace outline generate --book my_novel_v1 --rerun --from-phase phase_04_transition_causality_refinement --to-phase phase_06_thread_payoff_refinement`
- Resume only phase 4a and restart at first non-success chapter:
  - `bookforge --workspace workspace outline generate --book my_novel_v1 --resume --from-phase phase_04a_transition_seam_analysis --to-phase phase_04a_transition_seam_analysis`
- Force full rerun of chapter-scoped phases in selected range:
  - `bookforge --workspace workspace outline generate --book my_novel_v1 --resume --from-phase phase_04a_transition_seam_analysis --to-phase phase_06_thread_payoff_refinement --force-phase-full-rerun`
- With prompt file:
  - `bookforge --workspace workspace outline generate --book my_novel_v1 --prompt-file prompts\outline_seed.md`

Related commands
- `bookforge workflow init` (initialize section workflow state from outline artifacts)
- `bookforge workflow freeze-section` (promote one section into canonical outline state)
- `bookforge workflow advance-section` (freeze -> write -> lock one section end to end)
- `bookforge outline backup` (preserve a completed run-derived outline snapshot and artifacts)
- `bookforge outline restore` (recover `outline.json` from run id or backup snapshot)
