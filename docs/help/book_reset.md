# bookforge book reset

Purpose
- Reset a book's draft state so you can run a fresh test without re-initializing the book.

Usage
- bookforge book reset --book <id>

Scope
- Requires --book.

Required parameters
- --book: Book id slug.

Optional parameters
- --workspace: Override workspace root (global option).

What gets reset
- draft/chapters is cleared and recreated.
- draft/context/continuity_pack.json is removed.
- draft/context/bible.md and draft/context/last_excerpt.md are emptied.
- state.json is reset to a clean cursor/world state (budgets preserved).

What stays intact
- book.json, prompts, outline, canon, and exports.

Examples
- Minimal:
  bookforge book reset --book my_novel_v1
- With optional parameters:
  bookforge --workspace workspace book reset --book my_novel_v1
