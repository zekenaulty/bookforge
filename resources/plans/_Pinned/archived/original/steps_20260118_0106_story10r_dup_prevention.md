Goal
- Lock Story 10.R decisions for opening preview and pre-generation duplication prevention.

Context
- User confirmed opening preview requirements and requested machine-detectable formatting for stripping.

Commands
- None.

Files
- resources/plans/bookforge_plan_v2.md
- resources/plans/steps_20260118_0106_story10r_dup_prevention.md

Tests
- Not run (planning change only).

Issues
- None.

Decision
- Opening preview must be wrapped in explicit BEGIN/END tags for regex stripping.
- Opening preview content is excluded from word/page count thresholds and compile output.
- Opening preview includes 3-6 sentences + 3-5 bullet outline; must introduce a new concrete event.
- Banned phrase list derived from last N scenes with a max list size; regenerate on failure.

Completion
- Story 10.R accepted and locked.

Next Actions
- Proceed to Story 11.R refinement (lint, repair, and similarity checks).
