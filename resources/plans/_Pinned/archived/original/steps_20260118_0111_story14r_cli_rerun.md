Goal
- Lock Story 14.R decisions for CLI orchestration, rerun controls, and help docs coverage.

Context
- User confirmed scope validation, rerun flags, mutation rules, and complete help docs with examples.

Commands
- None.

Files
- resources/plans/bookforge_plan_v2.md
- resources/plans/steps_20260118_0111_story14r_cli_rerun.md

Tests
- Not run (planning change only).

Issues
- None.

Decision
- book set-current/show-current/clear-current commands are required.
- Rerun flags: --resume, --rerun-phase <phase>, --new-version.
- Mutation rules: outline generate immutable unless --new-version; run append-only; repair rewrite-with-archive.
- All book-scoped commands require explicit scope validation.
- docs/help must include full examples with and without optional parameters for every command.

Completion
- Story 14.R accepted and locked.

Next Actions
- Proceed to Story 15.R refinement (observability and prompt hashing).
