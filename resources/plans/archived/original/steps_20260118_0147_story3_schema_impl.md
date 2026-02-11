Goal
- Implement Story 3 schema versioning and validation.

Context
- Story 3 from bookforge_plan_v2.md.

Commands
- None.

Files
- schemas/book.schema.json
- schemas/state.schema.json
- schemas/outline.schema.json
- schemas/scene_card.schema.json
- schemas/state_patch.schema.json
- schemas/lint_report.schema.json
- src/bookforge/util/schema.py
- src/bookforge/util/__init__.py
- tests/test_schema_validation.py
- pyproject.toml
- resources/plans/steps_20260118_0147_story3_schema_impl.md

Tests
- Not run (tests added).

Issues
- None.

Decision
- Use jsonschema Draft 2020-12 for validation.
- Schemas require schema_version = 1.0 and enforce required fields with additionalProperties allowed.

Completion
- Story 3 completed.

Next Actions
- Proceed to Story 4 implementation (prompt templates and registry).
