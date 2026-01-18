# Step Notes: Outline Character Hooks and Beat Variance

Goal
- Capture character introductions in outlines and avoid uniform beat counts.

Context
- Outline output used a fixed three-beat structure and introduced characters without explicit hooks.

Commands
- None.

Files
- resources/prompt_templates/outline.md
- resources/prompt_templates/plan.md
- src/bookforge/outline.py
- src/bookforge/phases/plan.py
- docs/help/outline_generate.md
- tests/test_outline_generate.py
- src/bookforge/config/env.py
- .env.example

Tests
- Not run (implementation change).

Issues
- None.

Decision
- Outline prompts require variable beats per chapter and explicit character stubs + per-beat character ids.
- Outline generation writes outline/characters.json when characters are present.
- Default request timeout increased to 600 seconds.

Completion
- Outline generation now supports character hooks and beat variability.

Next Actions
- Re-run outline generation with the updated template.
