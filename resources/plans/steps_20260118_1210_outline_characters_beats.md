# Step Notes: Outline Character Hooks and Section/Scene Variance

Goal
- Capture character introductions in outlines and avoid uniform scene counts.

Context
- Outline output used a fixed three-scene structure and introduced characters without explicit hooks.

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
- Outline prompts require sections per chapter with variable scene counts and explicit character stubs + per-scene character ids (aim 6-32 based on chapter complexity).
- Outline summaries should remain concise but reflect the author voice.
- Outline generation writes outline/characters.json when characters are present.
- Plan step raises when scene_number exceeds available scenes (avoids reuse).
- Default request timeout increased to 600 seconds.

Completion
- Outline generation now supports character hooks and scene variability.

Next Actions
- Re-run outline generation with the updated template.
