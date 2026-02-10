# Step Notes: Story 8 Outline and Scene Planning

Goal
- Implement outline generation and the plan step that produces scene cards.

Context
- Story 8 requires outline.json creation, per-chapter outline files, and scene card planning for the next scene.

Commands
- None.

Files
- src/bookforge/outline.py
- src/bookforge/phases/plan.py
- src/bookforge/cli.py
- src/bookforge/workspace.py
- resources/prompt_templates/outline.md
- resources/prompt_templates/plan.md
- resources/prompt_registry.json
- docs/help/outline_generate.md
- tests/test_outline_generate.py
- tests/test_plan_scene.py

Tests
- Not run (implementation change).

Issues
- None.

Decision
- Outline generation uses prompts/system_v1.md and prompts/templates/outline.md with JSON-only output.
- Scene planning uses prompts/templates/plan.md and writes scene card JSON under draft/chapters/ch_###/scene_###.meta.json.
- LLM responses are logged on failure (or always when BOOKFORGE_LOG_LLM=1).

Completion
- outline generate writes outline.json + chapter files and updates state.json.
- plan_scene produces a validated scene card and updates state cursor + plan pointer.

Next Actions
- Run tests.
