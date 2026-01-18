# Step Notes: Outline JSON Repair

Goal
- Make outline generation resilient to LLM JSON boundary errors between chapters and before top-level metadata.

Context
- Outline generation failed with “Invalid JSON in response” even when output looked complete.
- Logged output showed missing chapter object boundaries and missing closure of the chapters array before top-level threads/characters.

Commands
- python -m pytest tests/test_outline_generate.py

Files
- src/bookforge/outline.py
- tests/test_outline_generate.py

Tests
- python -m pytest tests/test_outline_generate.py (failed: pytest not installed)

Issues
- LLM output omitted `}, {` between chapters and `}]` before top-level `threads`/`characters`, leaving unclosed braces/brackets.

Decision
- Add a repair pass for common outline JSON boundary mistakes, then attempt JSON parse again.
- Add a focused unit test that simulates the missing-boundary JSON case.

Completion
- Implemented `_repair_outline_json` and stack-based closer append to recover from missing boundaries.
- Added test coverage for repaired chapter boundaries.

Next Actions
- Install pytest and rerun outline tests.
- Re-run outline generation against the Gemini client to confirm repair path handles real outputs.
