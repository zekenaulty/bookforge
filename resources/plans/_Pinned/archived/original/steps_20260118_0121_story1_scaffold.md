Goal
- Scaffold the repo with packaging, CLI skeleton, docs/help, and workspace placeholders.

Context
- Story 1 from bookforge_plan_v2.md.

Commands
- python -m venv .venv (timed out but environment created)

Files
- .gitignore
- .env.example
- pyproject.toml
- src/bookforge/__init__.py
- src/bookforge/cli.py
- src/bookforge/runner.py
- src/bookforge/config/__init__.py
- src/bookforge/llm/__init__.py
- src/bookforge/prompt/__init__.py
- src/bookforge/memory/__init__.py
- src/bookforge/phases/__init__.py
- src/bookforge/compile/__init__.py
- src/bookforge/util/__init__.py
- docs/help/index.md
- docs/help/init.md
- docs/help/author_generate.md
- docs/help/outline_generate.md
- docs/help/characters_generate.md
- docs/help/run.md
- docs/help/compile.md
- docs/help/export_synopsis.md
- docs/help/book_set_current.md
- docs/help/book_show_current.md
- docs/help/book_clear_current.md
- workspace/.gitkeep
- workspace/authors/.gitkeep
- workspace/books/.gitkeep

Tests
- Not run (scaffolding only).

Issues
- venv creation command timed out but .venv directory exists.

Decision
- Added a CLI skeleton aligned to help docs and planned flags.
- Added docs/help with full examples including optional parameters.
- Added workspace placeholders without committing current_book.json.

Completion
- Story 1 completed.

Next Actions
- Proceed to Story 2 implementation (LLM provider layer).
