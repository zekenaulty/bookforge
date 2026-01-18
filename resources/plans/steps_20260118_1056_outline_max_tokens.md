# Step Notes: Outline Max Tokens Default

Goal
- Increase default outline max tokens to reduce truncation failures.

Context
- Outline generation hit MAX_TOKENS at 4096 and returned truncated JSON.

Commands
- None.

Files
- src/bookforge/outline.py
- docs/help/outline_generate.md

Tests
- Not run (config change).

Issues
- None.

Decision
- Default BOOKFORGE_OUTLINE_MAX_TOKENS set to 36864 (expanded for high-variance outlines).

Completion
- Outline default token cap increased and docs updated.

Next Actions
- Re-run outline generation; adjust via env var if still truncated.
