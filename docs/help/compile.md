# bookforge compile

Status
- Not implemented yet (CLI returns "Not implemented yet.").

Purpose
- Compile scene files into a single manuscript.

Usage
- bookforge compile --book <id> [--output <path>]

Scope
- Requires explicit --book (current-book selection is not implemented).

Required parameters
- --book: Book id slug.

Optional parameters
- --output: Output path for manuscript.
- --workspace: Override workspace root (global option).

Examples
- Minimal:
  bookforge compile --book my_novel_v1
- With optional parameters:
  bookforge --workspace workspace compile --book my_novel_v1 --output exports/manuscript.md