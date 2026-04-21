Goal
- Lock Story 13.R decisions for compile and export.

Context
- User confirmed compile behavior, opening preview stripping, synopsis sources, and output paths.

Commands
- None.

Files
- resources/plans/bookforge_plan_v2.md
- resources/plans/steps_20260118_0109_story13r_compile_export.md

Tests
- Not run (planning change only).

Issues
- None.

Decision
- Compile strips opening preview blocks by regex tags.
- Manuscript assembly adds chapter headings and preserves scene order/spacing.
- Synopsis export uses outline + bible (optional state.json).
- Outputs: exports/manuscript.md and exports/synopsis.md.

Completion
- Story 13.R accepted and locked.

Next Actions
- Proceed to Story 14.R refinement (CLI orchestration and rerun controls).
