# bookforge book list

Purpose
- List BookForge-owned book cards from the workspace.
- This is the engine-owned equivalent of Nanda's book-library fallback.

Usage
- `bookforge book list`
- `bookforge book list --json`

Behavior
- Reads each `workspace/books/<book_id>/book.json`.
- Enriches cards through BookForge query surfaces where possible:
  - current node
  - integrity status
  - branch count
  - chapter status counts
  - cursor location
- Falls back to minimal metadata if a book has incomplete state.

Output Notes
- JSON emits `book_card_v1` records.
- This is read-only and never mutates a book workspace.
