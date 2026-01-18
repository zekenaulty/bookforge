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

Examples
- Minimal:
  bookforge outline generate --book my_novel_v1
- With optional parameters:
  bookforge --workspace workspace outline generate --book my_novel_v1 --new-version
