# PLAN

You are the planner. Use the outline window and state to create the next scene card.
Return ONLY a single JSON object that matches the scene_card schema.
No markdown, no code fences, no commentary. Use strict JSON (double quotes, no trailing commas).

If outline_window includes character information, keep those character ids in mind.
If outline_window.current.introduces is present, the scene must introduce those characters.

Required keys:
- schema_version ("1.1")
- scene_id
- chapter
- scene
- scene_target
- goal
- conflict
- required_callbacks (array)
- constraints (array)
- end_condition

JSON shape example (fill with real values):
{
  "schema_version": "1.1",
  "scene_id": "SC_001_001",
  "chapter": 1,
  "scene": 1,
  "scene_target": "",
  "goal": "",
  "conflict": "",
  "required_callbacks": [],
  "constraints": [],
  "end_condition": ""
}

Outline window:
{{outline_window}}

State:
{{state}}

Task:
Create the next scene card.
