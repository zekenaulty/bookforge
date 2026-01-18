# bookforge book set-current

Purpose
- Set the current book for subsequent commands.

Usage
- bookforge book set-current --book <id>

Required parameters
- --book: Book id slug.

Optional parameters
- --workspace: Override workspace root (global option).

Examples
- Minimal:
  bookforge book set-current --book my_novel_v1
- With optional parameters:
  bookforge --workspace workspace book set-current --book my_novel_v1
