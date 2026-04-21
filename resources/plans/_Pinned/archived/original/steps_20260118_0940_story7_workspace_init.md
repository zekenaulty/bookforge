# Step Notes: Story 7 Workspace Init

Goal
- Implement the init command to scaffold a per-book workspace and system prompt.

Context
- Story 7 requires book/state defaults, prompt scaffolding, and author fragment pinning.

Commands
- None.

Files
- src/bookforge/workspace.py
- src/bookforge/cli.py
- docs/help/init.md
- tests/test_workspace_init.py

Tests
- Not run (implementation change).

Issues
- None.

Decision
- Default voice/invariants/page_metrics are applied at init and can be edited per book.
- System prompt is assembled from base rules, book constitution, author fragment, and output contract.

Completion
- init scaffolds workspace folders, book.json/state.json, prompts/templates, registry, and system_v1.md.

Next Actions
- Run tests.
