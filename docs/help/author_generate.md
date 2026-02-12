# bookforge author generate

Purpose
- Generate an author persona and store it in workspace/authors.

Usage
- bookforge author generate --influences "<name[:weight],...>" [--name "<persona_name>"] [--notes "<notes>"]
- bookforge author generate --prompt-file "<path>" [--name "<persona_name>"] [--notes "<notes>"]

Scope
- Author creation is global and not tied to a book.

Required parameters
- One of: --influences or --prompt-file.

Optional parameters
- --name: Optional author persona name. If omitted, the agent generates one.
- --notes: Optional notes or constraints.
- --workspace: Override workspace root (global option).


Debugging
- If the model returns invalid JSON, the raw response is written to workspace/logs/llm/author_generate_<timestamp>.json.
- To always log raw responses, set BOOKFORGE_LOG_LLM=1 before running.
  Example (PowerShell): $env:BOOKFORGE_LOG_LLM="1"

- If the output is truncated (MAX_TOKENS), raise BOOKFORGE_AUTHOR_MAX_TOKENS (default: 32768).
  Example (PowerShell): $env:BOOKFORGE_AUTHOR_MAX_TOKENS="32768"

Examples
- Minimal:
  bookforge author generate --influences "Brandon Sanderson:0.5,G.R.R. Martin:0.3,J.R.R. Tolkien:0.2"
- With optional parameters:
  bookforge --workspace workspace author generate --name "Eldrik Vale" --influences "Brandon Sanderson,G.R.R. Martin" --notes "Mythic tone with tight POV"
