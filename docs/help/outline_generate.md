# bookforge outline generate

Purpose
- Generate or regenerate the outline for a book.

Usage
- bookforge outline generate --book <id> [--new-version] [--prompt-file <path>]

Scope
- Requires book scope (explicit --book or current book).

Required parameters
- --book: Book id slug.

Optional parameters
- --new-version: Create a new outline version.
- --prompt-file: Path to a plain-English outline prompt file used as grounding context (relative to the current working directory).
- --workspace: Override workspace root (global option).

Outputs
- Writes outline/outline.json and outline/chapters/ch_###.json.
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
- If the output is truncated (MAX_TOKENS), raise BOOKFORGE_OUTLINE_MAX_TOKENS (default: 36864).
  Example (PowerShell): $env:BOOKFORGE_OUTLINE_MAX_TOKENS="36864"

- If requests time out, raise BOOKFORGE_REQUEST_TIMEOUT_SECONDS (default: 600).
  Example (PowerShell): $env:BOOKFORGE_REQUEST_TIMEOUT_SECONDS="600"

Examples
- Minimal:
  bookforge outline generate --book my_novel_v1
- With optional parameters:
  bookforge --workspace workspace outline generate --book my_novel_v1 --new-version
- With prompt file:
  bookforge --workspace workspace outline generate --book my_novel_v1 --prompt-file prompts\outline_seed.md
