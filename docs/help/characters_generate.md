# bookforge characters generate

Purpose
- Refine outline character stubs into canon character entries for a book.

Usage
- bookforge characters generate --book <id> [--count <n>]

Scope
- Requires book scope (explicit --book or current book).
- Reads outline/characters.json (or outline.json characters array) and series canon if present.
- Does not invent new characters; it expands only the outline-provided stubs.

Required parameters
- --book: Book id slug.

Optional parameters
- --count: Optional limit on the number of outline characters to refine.
- --workspace: Override workspace root (global option).

Outputs
- Writes canon/characters/<slug>.json entries for refined characters.
- Updates canon/index.json with character refs.

Examples
- Minimal:
  bookforge characters generate --book my_novel_v1
- With optional parameters:
  bookforge --workspace workspace characters generate --book my_novel_v1 --count 6
