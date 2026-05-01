# bookforge author

Purpose
- List, inspect, and generate BookForge-owned author personas under `workspace/authors`.

Usage
- bookforge author list [--json]
- bookforge author profile <author_ref> [--version <vN>] [--json]
- bookforge author generate --influences "<name[:weight],...>" [--name "<persona_name>"] [--notes "<notes>"]
- bookforge author generate --prompt-file "<path>" [--name "<persona_name>"] [--notes "<notes>"]
- bookforge author create [--name "<persona_name>"] [--influences "<name[:weight],...>" | --prompt-text "<brief>" | --prompt-file "<path>"] [--notes "<notes>"] [--json]
- bookforge author refine <author_ref> (--instructions "<changes>" | --prompt-file "<path>") [--notes "<notes>"] [--json]

Scope
- Author profiles are global assets and not tied to one book.
- A book may still pin a specific author version through `book.json.author_ref`, such as `eldrik-vale/v2`.
- Author creation/refinement uses workflow family `author_assets` and virtual selector book id `__author_library__`.
- `author create` and `author refine` emit `execution_result_v1` receipts and authoritative produced-artifact receipts.

Required parameters
- `author profile`: `<author_ref>`, such as `eldrik-vale` or `eldrik-vale/v2`.
- `author generate`: one of `--influences` or `--prompt-file`.
- `author create`: one of `--influences`, `--prompt-text`, or `--prompt-file`.
- `author refine`: `<author_ref>` and one of `--instructions` or `--prompt-file`.

Optional parameters
- `author list --json`: emit the machine-readable author profile list.
- `author profile --version`: override the version implied by `<author_ref>`.
- `author profile --json`: emit the full `author_profile_view_v1` payload.
- --name: Optional author persona name. If omitted, the agent generates one.
- --notes: Optional notes or constraints.
- --workspace: Override workspace root (global option).

Query contract
- Python:
  - `bookforge.query.list_author_profiles(workspace)`
  - `bookforge.query.get_author_profile(workspace, author_ref, version=None)`
  - `bookforge.execution.build_create_author_request(...)`
  - `bookforge.execution.create_author_action(workspace, request)`
  - `bookforge.execution.build_refine_author_request(...)`
  - `bookforge.execution.refine_author_action(workspace, request)`
- Author profile payloads expose:
  - `artifact_status=authoritative`
  - `author_ref`, `default_version`, and `selected_version`
  - voice, themes, sensory bias, pacing, style rules, cadence rules, taboos, banned phrases, influences
  - `style_markdown`, `system_fragment`, and derived `profile_markdown`
  - source paths for the underlying BookForge author files
- Nanda should render this surface directly instead of inventing author voice from a thin list record.
- Capability projection exposes:
  - `action.create_author`
  - `action.refine_author`
  - `query.author_profiles`
  - `query.author_profile`
- Refinement never overwrites an existing author version; it creates a successor version and updates the author index default version.

Debugging
- If the model returns invalid JSON, the raw response is written to workspace/logs/llm/author_generate_<timestamp>.json.
- To always log raw responses, set BOOKFORGE_LOG_LLM=1 before running.
  Example (PowerShell): $env:BOOKFORGE_LOG_LLM="1"

- If the output is truncated (MAX_TOKENS), raise BOOKFORGE_AUTHOR_MAX_TOKENS (default: 32768).
  Example (PowerShell): $env:BOOKFORGE_AUTHOR_MAX_TOKENS="32768"

Examples
- List authors:
  bookforge author list
- Show a rich profile:
  bookforge author profile eldrik-vale/v2
- Minimal:
  bookforge author generate --influences "Brandon Sanderson:0.5,G.R.R. Martin:0.3,J.R.R. Tolkien:0.2"
- With optional parameters:
  bookforge --workspace workspace author generate --name "Eldrik Vale" --influences "Brandon Sanderson,G.R.R. Martin" --notes "Mythic tone with tight POV"
- Create with a receipt:
  bookforge --workspace workspace author create --name "Eldrik Vale" --prompt-text "System-aware LitRPG author with dry menace and clean mechanics." --json
- Refine into a new version:
  bookforge --workspace workspace author refine eldrik-vale/v2 --instructions "Warm the emotional interiority while preserving precise system humor." --json
