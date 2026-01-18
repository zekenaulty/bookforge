# bookforge characters generate

Purpose
- Generate character canon entries for a book.

Usage
- bookforge characters generate --book <id> [--count <n>]

Scope
- Requires book scope (explicit --book or current book).

Required parameters
- --book: Book id slug.

Optional parameters
- --count: Optional limit on the number of characters to generate.
- --workspace: Override workspace root (global option).

Examples
- Minimal:
  bookforge characters generate --book my_novel_v1
- With optional parameters:
  bookforge --workspace workspace characters generate --book my_novel_v1 --count 6
