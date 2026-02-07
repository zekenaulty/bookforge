# bookforge book reset

Purpose
- Reset a book runtime workspace back to a clean post-outline baseline for reruns.

Usage
- `bookforge book reset --book <id> [--keep-logs] [--logs-scope book|all]`

Scope
- Requires `--book`.

Required parameters
- `--book`: Book id slug.

Optional parameters
- `--keep-logs`: Preserve `workspace/logs/llm` files.
- `--logs-scope`: When logs are cleared, remove only this book's logs (`book`, default) or all logs (`all`).
- `--workspace`: Override workspace root (global option).

What gets reset
- `state.json` is rewritten to clean cursor/world/summary state (budgets preserved, status set to `OUTLINED` when outline exists).
- `draft/chapters/*` is cleared and recreated.
- `draft/context/continuity_pack.json`, `draft/context/continuity_history/*`, `draft/context/chapter_summaries/*`, and `draft/context/run_paused.json` are removed.
- `draft/context/characters/*` is removed (character runtime state auto-regenerates on next run).
- Durable runtime canon is rebuilt:
  - `draft/context/item_registry.json`
  - `draft/context/plot_devices.json`
  - `draft/context/durable_commits.json`
  - `draft/context/items/*`
  - `draft/context/plot_devices/*`
- `draft/context/bible.md` and `draft/context/last_excerpt.md` are emptied.
- `exports/*` and book-local `logs/*` are cleared and recreated.

What stays intact
- `book.json`, prompts, outline, and immutable author/series assets.

Console summary
- The command prints deletion/recreation totals, including log file counts.

Examples
- Minimal:
  `bookforge book reset --book my_novel_v1`
- Preserve logs:
  `bookforge book reset --book my_novel_v1 --keep-logs`
- Clear all LLM logs in workspace while resetting:
  `bookforge book reset --book my_novel_v1 --logs-scope all`
- With workspace override:
  `bookforge --workspace workspace book reset --book my_novel_v1 --logs-scope book`
