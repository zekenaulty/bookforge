# Step Notes: Outline Sections and Scene Terminology

Goal
- Move the outline schema to sections + scenes and align terminology with scene-focused planning.

Context
- Beats encouraged under-sized outlines and ambiguous leaf units.
- The outline now needs chapter rhythm (sections) while keeping the leaf unit aligned with the writing loop (scene).

Decisions
- Outline schema v1.1: chapters contain sections, sections contain scenes; beat terminology removed.
- Scene fields include type and outcome to enforce concrete state change.
- Chapters include role, stakes shift, bridge, and pacing metadata.
- Characters and threads remain optional top-level lists and can be listed after chapters.
- Scene card uses scene_target instead of beat_target (schema v1.1).

Files
- resources/prompt_templates/outline.md
- resources/prompt_templates/plan.md
- schemas/outline.schema.json
- schemas/scene_card.schema.json
- src/bookforge/outline.py
- src/bookforge/phases/plan.py
- tests/test_outline_generate.py
- tests/test_plan_scene.py

Tests
- Not run (implementation change).

Issues
- None.

Completion
- Outline generation expects sections + scenes and planning uses scene terminology end-to-end.
