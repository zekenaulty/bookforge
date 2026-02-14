<!-- begin entry=E001 semantic=plan.scene_card_prompt_contract_and_schema source=resources/prompt_blocks/phase/plan/scene_card_prompt_contract_and_schema.md repeat=1/1 -->
# PLAN

You are the planner. Use the outline window and state to create the next scene card.
Return ONLY a single JSON object that matches the scene_card schema.
No markdown, no code fences, no commentary. Use strict JSON (double quotes, no trailing commas).

If outline_window includes character information, keep those character ids in mind.
If character_states are provided, keep inventory/persona/continuity mechanics consistent; do not invent conflicting facts.
If outline_window.current.introduces is present, the scene must introduce those characters.
If outline_window.section.end_condition is present, align scene-card end_condition to satisfy that closure target.
If outline_window.current includes transition payload/link fields, copy them through into the scene card verbatim where possible. Do not re-derive or rename.
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
- location_start
- location_end
- handoff_mode
- constraint_state
- transition_in_text
- transition_in_anchors (array of 3-6 strings)
- seam_score (0-100 integer)
- seam_resolution ("inline_bridge"|"micro_scene"|"full_scene")

Required when present in outline_window.current:
- consumes_outcome_from
- hands_off_to
- transition_out
- hard_cut_justification
- intentional_cinematic_cut

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
  "location_start": "North Gate Checkpoint",
  "location_end": "Barnaby's Tavern",
  "handoff_mode": "detained_then_release",
  "constraint_state": "processed",
  "transition_in_text": "After a brief detention and scanner review, the guards release Artie under watch and direct him to Barnaby's Tavern.",
  "transition_in_anchors": ["detention", "scanner", "release", "guards", "tavern"],
  "transition_out": "Artie enters Barnaby's under scrutiny and without leverage.",
  "consumes_outcome_from": "1:6",
  "hands_off_to": "1:8",
  "seam_score": 78,
  "seam_resolution": "micro_scene",
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
<!-- end entry=E001 semantic=plan.scene_card_prompt_contract_and_schema -->
