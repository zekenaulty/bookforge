# bookforge outline generate

Purpose
- Generate or regenerate the outline for a book.

Usage
- bookforge outline generate --book <id> [--new-version]

Scope
- Requires book scope (explicit --book or current book).

Required parameters
- --book: Book id slug.

Optional parameters
- --new-version: Create a new outline version.
- --workspace: Override workspace root (global option).

Outputs
- Writes outline/outline.json and outline/chapters/ch_###.json.
- If the outline includes characters, writes outline/characters.json.
- Updates state.json with outline path and status when applicable.

Debugging
- If the model returns invalid JSON, the raw response is written to workspace/logs/llm/outline_generate_<timestamp>.json.
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
