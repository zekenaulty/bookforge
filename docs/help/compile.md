# bookforge compile

Purpose
- Compile scene files into a single manuscript.

Usage
- bookforge compile --book <id> [--output <path>]

Scope
- Requires book scope (explicit --book or current book).

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
