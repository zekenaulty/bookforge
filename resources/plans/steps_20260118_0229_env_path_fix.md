Goal
- Ensure .env is loaded from the repo root when running CLI from any directory.

Context
- Author generation used default openai because .env was not found relative to the current working directory.

Commands
- .\.venv\Scripts\python -m pytest -q

Files
- src/bookforge/config/env.py
- resources/plans/steps_20260118_0229_env_path_fix.md

Tests
- 23 passed in 0.21s

Issues
- None.

Decision
- load_config now resolves .env relative to the repo root when env is not supplied.
- env_path=None with explicit env dict skips file loading (keeps tests deterministic).

Completion
- .env resolution now stable across working directories.
