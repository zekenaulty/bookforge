Goal
- Lock Story 12.R decisions for canon store and retrieval rules.

Context
- User confirmed canon schemas, index mapping, injection rules, and update constraints.

Commands
- None.

Files
- resources/plans/bookforge_plan_v2.md
- resources/plans/steps_20260118_0108_story12r_canon_retrieval.md

Tests
- Not run (planning change only).

Issues
- None.

Decision
- Canon schemas for character, location, rule, thread include id, summary, tags, updated_at.
- canon/index.json maps id to path, tags, short description, and priority.
- Inject canon referenced by scene card + state, with size caps.
- Canon updates only via explicit state patch or canon update step.

Completion
- Story 12.R accepted and locked.

Next Actions
- Proceed to Story 13.R refinement (compile and export).
