Goal
- Lock Story 1.R decisions for scope resolution and help docs.

Context
- User approved explicit scope rules with current_book.json and verbose docs in docs/help.

Commands
- None.

Files
- resources/plans/bookforge_plan_v2.md
- resources/plans/steps_${ts}_story1r_scope_help.md

Tests
- Not run (planning change only).

Issues
- None.

Decision
- Add workspace/current_book.json with book_id and book_path.
- Add CLI commands: book set-current, book show-current, book clear-current.
- Scope resolution uses --book when present; otherwise current_book.json; error if neither.
- Help docs live in docs/help with per-command verbose examples.

Completion
- Story 1.R accepted and locked.

Next Actions
- Proceed to Story 2.R refinement (LLM provider abstraction).
