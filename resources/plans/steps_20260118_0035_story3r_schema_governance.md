Goal
- Lock Story 3.R decisions for schema governance and validation.

Context
- User confirmed JSON Schema, schema_version, hard validation, and required schemas.

Commands
- None.

Files
- resources/plans/bookforge_plan_v2.md
- resources/plans/steps_20260118_0035_story3r_schema_governance.md

Tests
- Not run (planning change only).

Issues
- None.

Decision
- Schemas live in schemas/ and every artifact includes schema_version.
- Validation is a hard fail; repair is only for LLM outputs.
- Required v1 schemas: book, state, outline, scene_card, state_patch, lint_report.
- continuity_pack will be formalized later with the budgeter/continuity work.

Completion
- Story 3.R accepted and locked.

Next Actions
- Proceed to Story 4.R refinement (prompt system and caching rules).
