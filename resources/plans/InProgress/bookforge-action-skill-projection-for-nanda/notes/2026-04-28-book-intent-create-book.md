# 2026-04-28 BookIntent/Create-Book Bridge

Status: implemented initial slice.

Problem
- Nanda could capture author-only `book_seed` material but BookForge still advertised book intent/synopsis as a designed gap.
- There was no receipt-backed transition from author-only ideation into a canonical BookForge book workspace.

Changes
- Added `BookIntent` query surfaces:
  - `bookforge.query.list_book_intents(...)`
  - `bookforge.query.get_book_intent(...)`
- Added execution actions:
  - `draft_book_intent`
  - `approve_book_intent`
  - `create_book_from_intent`
- Added CLI:
  - `bookforge book intent list`
  - `bookforge book intent show`
  - `bookforge book intent draft`
  - `bookforge book intent approve`
  - `bookforge book intent create`
- Replaced `gap.book_intent.synopsis` with implemented capability descriptors and query descriptors.
- `create_book_from_intent` now writes a canonical book workspace, copies the intent into the book, seeds `draft/context/book_intent.md`, seeds empty `bible.md`, and regenerates prompts.

Truth Model
- Draft intent: provisional, reviewable, not a book.
- Approved intent: authoritative creation source.
- Created intent: canonical book workspace exists and the transition is backed by an execution receipt.

Validation
- Added `tests/test_book_intent_actions.py`.
- Focused validation passed:
  - `python -m pytest tests/test_book_intent_actions.py tests/test_capability_projection.py tests/test_scope_contracts.py -q`
  - `python -m compileall -q src tests`

Nanda Impact
- Nanda can now replace the blocked `book_seed` promotion path with BookForge-owned `BookIntent` actions.
- The author-only chat should draft an intent, request approval, create the book, then switch to book-scoped authoring only after `create_book_from_intent` returns a success receipt.
