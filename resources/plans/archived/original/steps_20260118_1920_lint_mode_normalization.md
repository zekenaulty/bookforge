# Step Notes: Lint Mode and Normalization

Goal
- Make lint outputs tolerant of model variability and allow lint to be relaxed or disabled.

Context
- LLM lint output often omits required keys; we need a normalization shim and a runtime lint mode switch.

Commands
- None.

Files
- src/bookforge/runner.py
- resources/prompt_templates/lint.md
- workspace/books/sagefall_p1_v1/prompts/templates/lint.md
- docs/help/run.md
- README.md
- .env.example

Tests
- Not run (behavior and docs change).

Issues
- None.

Decision
- BOOKFORGE_LINT_MODE controls lint behavior: strict, warn, off.
- Lint reports are normalized to include status/issues even when the model returns alternate fields.

Completion
- Lint no longer fails on missing status when the model returns pass/violations/warnings.
- Runs can proceed with lint disabled or non-blocking.

Next Actions
- Run tests.
