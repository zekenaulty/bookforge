# bookforge export synopsis

Purpose
- Generate a synopsis from outline and bible.

Usage
- bookforge export synopsis --book <id> [--output <path>]

Scope
- Requires book scope (explicit --book or current book).

Required parameters
- --book: Book id slug.

Optional parameters
- --output: Output path for synopsis.
- --workspace: Override workspace root (global option).

Examples
- Minimal:
  bookforge export synopsis --book my_novel_v1
- With optional parameters:
  bookforge --workspace workspace export synopsis --book my_novel_v1 --output exports/synopsis.md
