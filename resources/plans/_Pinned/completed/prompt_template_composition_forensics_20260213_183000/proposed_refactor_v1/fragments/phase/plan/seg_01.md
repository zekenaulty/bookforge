# PLAN

You are the planner. Use the outline window and state to create the next scene card.
Return ONLY a single JSON object that matches the scene_card schema.
No markdown, no code fences, no commentary. Use strict JSON (double quotes, no trailing commas).

If outline_window includes character information, keep those character ids in mind.
If character_states are provided, keep inventory/persona/continuity mechanics consistent; do not invent conflicting facts.
If outline_window.current.introduces is present, the scene must introduce those characters.
If recent_lint_warnings include ui_gate_unknown, set ui_allowed explicitly for this scene.

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
- ui_allowed (boolean; true only when System/UI is active in this scene)

Recommended keys (use ids from the outline; do not invent ids):
- cast_present (array of character names for prose guidance)
- cast_present_ids (array of character ids, e.g. CHAR_Eldrin)
- introduces (array of character names introduced in this scene)
- introduces_ids (array of character ids introduced in this scene)
- thread_ids (array of thread ids, e.g. THREAD_Awakened_Sage)

Optional continuity-planning keys:
- required_in_custody (array of item/device ids that must still be owned by scene start)
- required_scene_accessible (array of item/device ids that must be retrievable without continuity break)
- required_visible_on_page (array of ids that must be explicitly shown in-scene; use sparingly)
- forbidden_visible (array of ids that must not be visibly carried/active in-scene)
- device_presence (array of plot-device ids expected to matter in-scene)
- transition_type (string, e.g. "time_skip", "travel_arrival", "combat_aftermath")
- timeline_scope ("present"|"flashback"|"dream"|"simulation"|"hypothetical")
- ontological_scope ("real"|"non_real")

Optional genre/system keys:
- continuity_system_focus (array of mechanic domains likely to change this scene, e.g. ["stats", "resources", "titles"])
- ui_mechanics_expected (array of UI labels likely to appear, e.g. ["HP", "Stamina", "Crit Rate"])
  - If ui_allowed=false, ui_mechanics_expected MUST be an empty array.

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
  "constraints": ["target_words: 1900"],
  "end_condition": "The protagonist leaves home.",
  "ui_allowed": false,
  "cast_present": ["Eldrin"],
  "cast_present_ids": ["CHAR_Eldrin"],
  "introduces": [],
  "introduces_ids": [],
  "thread_ids": ["THREAD_Awakened_Sage"],
  "required_in_custody": ["ITEM_broken_tutorial_sword"],
  "required_scene_accessible": ["ITEM_broken_tutorial_sword"],
  "required_visible_on_page": [],
  "forbidden_visible": [],
  "device_presence": ["DEVICE_anomaly_tag"],
  "transition_type": "travel_arrival",
  "timeline_scope": "present",
  "ontological_scope": "real",
  "continuity_system_focus": ["stats", "resources"],
  "ui_mechanics_expected": ["HP", "Stamina"]
}

Outline window:
{{outline_window}}

Character states (per outline_window.current.characters):
{{character_states}}

State:
{{state}}

Recent lint warnings (prior scene, if any):
{{recent_lint_warnings}}

Task:
Create the next scene card.


