# Step Notes: Series Canon Scaffolding

Goal
- Treat every book as part of a series by seeding a series-level canon namespace.

Context
- Cross-book continuity is future scope, but we need a shared series folder now for character carryover.
- If no series id is provided, the system should generate one and keep it consistent for the book.

Decisions
- Default series_id to the book_id when not provided.
- Always set series_ref to series/<series_id> in book.json.
- Create workspace/series/<series_id>/series.json and canon/ scaffolding on init.

Files
- src/bookforge/workspace.py
- docs/help/init.md
- tests/test_workspace_init.py

Tests
- Not run (plan/update change).

Issues
- None.

Completion
- Series workspace is created during init and book.json always has series_id/series_ref.
