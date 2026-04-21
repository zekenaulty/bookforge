# Step Notes: Outline Prompt File Support

Goal
- Allow outline generation to accept a user-provided prompt file for guided outlining.

Context
- Users want to supply a plain-English book summary (characters, world, systems) that grounds the outline while keeping the schema rules.

Commands
- None.

Files
- src/bookforge/cli.py
- src/bookforge/outline.py
- resources/prompt_templates/outline.md
- docs/help/outline_generate.md
- tests/test_outline_generate.py

Tests
- Not run (implementation change).

Issues
- None.

Decision
- Add --prompt-file to outline generate.
- If provided, the file content is appended to the outline prompt as user guidance.
- Outline prompt keeps author voice via system_v1.md.

Completion
- Outline generation can be guided by a user prompt file without changing default behavior.
