Goal
- Lock Story 7.R decisions for workspace init and book/state schemas.

Context
- User confirmed required book.json/state.json fields, init inputs, and system prompt assembly.

Commands
- None.

Files
- resources/plans/bookforge_plan_v2.md
- resources/plans/steps_20260118_0053_story7r_workspace_schema.md

Tests
- Not run (planning change only).

Issues
- None.

Decision
- book.json required: book_id, title, genre, targets, voice, invariants, author_ref; optional series_id and series_ref.
- state.json required: status, cursor, world (time, location, cast_present, open_threads, recent_facts), budgets, duplication_warnings_in_row.
- init inputs: --book, --author-ref, --title, --genre, --targets (optional), --series-id (optional).
- init assembles prompts/system_v1.md from base rules + book constitution + author fragment.

Completion
- Story 7.R accepted and locked.

Next Actions
- Proceed to Story 8.R refinement (outline and scene card schemas).
