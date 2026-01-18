Goal
- Implement Story 6 author creation pipeline.

Context
- Story 6 from bookforge_plan_v2.md.

Commands
- .\.venv\Scripts\python -m pytest -q

Files
- src/bookforge/author.py
- src/bookforge/cli.py
- resources/prompt_templates/author_generate.md
- tests/test_author_index.py
- resources/plans/steps_20260118_0222_story6_author_impl.md

Tests
- 23 passed in 0.25s

Issues
- None.

Decision
- Author generation uses the active LLM provider and planner model.
- Outputs are stored under workspace/authors/<slug>/vN with index.json per author.
- Optional banned_phrases are stored in author.json when provided.

Completion
- Story 6 completed.

Next Actions
- Proceed to Story 7 implementation (workspace init and book schema).
