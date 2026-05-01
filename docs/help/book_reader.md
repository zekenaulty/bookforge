# bookforge book reader

Purpose
- Read canonical BookForge prose and nearby outline metadata by book, chapter, or scene.
- This replaces Nanda's direct filesystem reader fallback with an engine-owned query surface.

Usage
- `bookforge book reader --book <id>`
- `bookforge book reader --book <id> --chapter <n>`
- `bookforge book reader --book <id> --chapter <n> --scene <s>`
- `bookforge book reader --book <id> --branch-id <branch>`
- `bookforge book reader --book <id> --chapter <n> --scene <s> --json`
- `bookforge book reader-anchor --book <id> --chapter <n> --scene <s> --start-offset <n> --end-offset <n> --json`
- `bookforge book reader-anchor --book <id> --branch-id <branch> --chapter <n> --scene <s> --json`

Behavior
- Uses `bookforge.query.get_book_reader_view(...)`.
- Anchor queries use `bookforge.query.get_book_reader_anchor(...)`.
- Reads main by default.
- If `--branch-id` is provided, reads the branch snapshot and marks the reader view as branch-scoped.
- Reports artifact status for selected prose:
  - `authoritative` when prose exists as a committed reader artifact in that scope.
  - `diagnostic` when the selected prose artifact is missing.
- Reader anchors add mutation-safety evidence for a selected span:
  - source path relative to canonical and execution roots
  - full source hash
  - selected span offsets and selected hash
  - canonical vs branch reader status
  - whether the selected span is safe to use as a mutation target

Scope Notes
- Reader queries are read-only.
- A scene-level reader anchor can be used as a mutation target for branch-local authoring tools.
- A chapter-level reader anchor is inspect-only until narrowed to a scene.
- A reader anchor proves source and span; it does not execute a rewrite.
- For contaminated books, pair reader output with integrity and outline lineage queries before making repair decisions.
