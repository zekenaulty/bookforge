Goal
- Lock Story 16.R decisions for tests and documentation.

Context
- User confirmed test matrix and docs requirements, with skepticism on testability.

Commands
- None.

Files
- resources/plans/bookforge_plan_v2.md
- resources/plans/steps_20260118_0115_story16r_tests_docs.md

Tests
- Not run (planning change only).

Issues
- Testing will require robust mocks to hit edge cases.

Decision
- Test matrix includes schema validation, prompt determinism, budgeter reporting, duplication checks, opening preview gate, compile ordering.
- Docs include README updates and docs/help with full examples including optional flags.
- Add a verification checklist doc for manual runs.
- Testing approach will rely on strong mocks and fixtures to cover LLM edge cases.

Completion
- Story 16.R accepted and locked.

Next Actions
- Refinements complete; begin implementation with Story 1 scaffolding.
