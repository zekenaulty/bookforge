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

Recommended keys (use ids from the outline; do not invent ids):
- cast_present (array of character names for prose guidance)
- cast_present_ids (array of character ids, e.g. CHAR_Eldrin)
- introduces (array of character names introduced in this scene)
- introduces_ids (array of character ids introduced in this scene)
- thread_ids (array of thread ids, e.g. THREAD_Awakened_Sage)

JSON shape example (fill with real values):
{
  "schema_version": "1.1",
  "scene_id": "SC_001_001",
  "chapter": 1,
  "scene": 1,
  "scene_target": "Protagonist commits to the journey.",
  "goal": "Force a decisive choice.",
  "conflict": "Safety versus obligation.",
  "required_callbacks": [],
  "constraints": ["target_words: 900"],
  "end_condition": "The protagonist leaves home.",
  "cast_present": ["Eldrin"],
  "cast_present_ids": ["CHAR_Eldrin"],
  "introduces": [],
  "introduces_ids": [],
  "thread_ids": ["THREAD_Awakened_Sage"]
}

Outline window:
{{outline_window}}

State:
{{state}}

Task:
Create the next scene card.
