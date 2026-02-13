# Snapshot: plan.md

- Source: `resources/prompt_templates/plan.md`
- SHA256: `65A7BF57348EDC1596EE9FFD8F8DF87B9D98E5CC08173E15A784773D1980C194`
- Line count: `91`
- Byte length: `3604`

```text
   1: # PLAN
   2: 
   3: You are the planner. Use the outline window and state to create the next scene card.
   4: Return ONLY a single JSON object that matches the scene_card schema.
   5: No markdown, no code fences, no commentary. Use strict JSON (double quotes, no trailing commas).
   6: 
   7: If outline_window includes character information, keep those character ids in mind.
   8: If character_states are provided, keep inventory/persona/continuity mechanics consistent; do not invent conflicting facts.
   9: If outline_window.current.introduces is present, the scene must introduce those characters.
  10: If recent_lint_warnings include ui_gate_unknown, set ui_allowed explicitly for this scene.
  11: 
  12: Required keys:
  13: - schema_version ("1.1")
  14: - scene_id
  15: - chapter
  16: - scene
  17: - scene_target
  18: - goal
  19: - conflict
  20: - required_callbacks (array)
  21: - constraints (array)
  22: - end_condition
  23: - ui_allowed (boolean; true only when System/UI is active in this scene)
  24: 
  25: Recommended keys (use ids from the outline; do not invent ids):
  26: - cast_present (array of character names for prose guidance)
  27: - cast_present_ids (array of character ids, e.g. CHAR_Eldrin)
  28: - introduces (array of character names introduced in this scene)
  29: - introduces_ids (array of character ids introduced in this scene)
  30: - thread_ids (array of thread ids, e.g. THREAD_Awakened_Sage)
  31: 
  32: Optional continuity-planning keys:
  33: - required_in_custody (array of item/device ids that must still be owned by scene start)
  34: - required_scene_accessible (array of item/device ids that must be retrievable without continuity break)
  35: - required_visible_on_page (array of ids that must be explicitly shown in-scene; use sparingly)
  36: - forbidden_visible (array of ids that must not be visibly carried/active in-scene)
  37: - device_presence (array of plot-device ids expected to matter in-scene)
  38: - transition_type (string, e.g. "time_skip", "travel_arrival", "combat_aftermath")
  39: - timeline_scope ("present"|"flashback"|"dream"|"simulation"|"hypothetical")
  40: - ontological_scope ("real"|"non_real")
  41: 
  42: Optional genre/system keys:
  43: - continuity_system_focus (array of mechanic domains likely to change this scene, e.g. ["stats", "resources", "titles"])
  44: - ui_mechanics_expected (array of UI labels likely to appear, e.g. ["HP", "Stamina", "Crit Rate"])
  45:   - If ui_allowed=false, ui_mechanics_expected MUST be an empty array.
  46: 
  47: JSON shape example (fill with real values):
  48: {
  49:   "schema_version": "1.1",
  50:   "scene_id": "SC_001_001",
  51:   "chapter": 1,
  52:   "scene": 1,
  53:   "scene_target": "Protagonist commits to the journey.",
  54:   "goal": "Force a decisive choice.",
  55:   "conflict": "Safety versus obligation.",
  56:   "required_callbacks": [],
  57:   "constraints": ["target_words: 1900"],
  58:   "end_condition": "The protagonist leaves home.",
  59:   "ui_allowed": false,
  60:   "cast_present": ["Eldrin"],
  61:   "cast_present_ids": ["CHAR_Eldrin"],
  62:   "introduces": [],
  63:   "introduces_ids": [],
  64:   "thread_ids": ["THREAD_Awakened_Sage"],
  65:   "required_in_custody": ["ITEM_broken_tutorial_sword"],
  66:   "required_scene_accessible": ["ITEM_broken_tutorial_sword"],
  67:   "required_visible_on_page": [],
  68:   "forbidden_visible": [],
  69:   "device_presence": ["DEVICE_anomaly_tag"],
  70:   "transition_type": "travel_arrival",
  71:   "timeline_scope": "present",
  72:   "ontological_scope": "real",
  73:   "continuity_system_focus": ["stats", "resources"],
  74:   "ui_mechanics_expected": ["HP", "Stamina"]
  75: }
  76: 
  77: Outline window:
  78: {{outline_window}}
  79: 
  80: Character states (per outline_window.current.characters):
  81: {{character_states}}
  82: 
  83: State:
  84: {{state}}
  85: 
  86: Recent lint warnings (prior scene, if any):
  87: {{recent_lint_warnings}}
  88: 
  89: Task:
  90: Create the next scene card.
  91: 
```
