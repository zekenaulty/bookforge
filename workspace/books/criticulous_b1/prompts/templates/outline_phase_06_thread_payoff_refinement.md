# OUTLINE PIPELINE PHASE 06: THREAD AND PAYOFF REFINEMENT

Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.

Return ONLY a single JSON object matching outline schema v1.1.
No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Goal:
- Produce final release-ready outline with thread cadence and bridge coherence.
- Preserve transition and cast integrity from prior phases.

Required top-level keys:
- schema_version ("1.1")
- chapters (array)

Registry policy:
- characters and threads are globally optional, but become REQUIRED when referenced.
- If any scene references character ids (characters/introduces/callbacks), top-level characters is required.
- If any scene references thread ids, top-level threads is required.
- Use canonical registry keys only. Do not use alias keys.
  - characters[] required keys and types:
    - character_id (string)
    - name (string)
    - intro (object with chapter integer >=1 and scene integer >=1)
  - threads[] required keys and types:
    - thread_id (string)
    - label (string)
    - status (string)
- Forbidden aliases:
  - characters[].id, characters[].title, characters[].description
  - threads[].id, threads[].title, threads[].description

Required integrity:
- Keep chapter_id sequential and scene_id monotonic chapter-local.
- Chapter objects must include required keys and correct types:
  - chapter_id (integer), title (string), goal (string), chapter_role (string), stakes_shift (string)
  - bridge (object with from_prev string, to_next string)
  - pacing (object with intensity number|string, tempo string, expected_scene_count integer)
  - sections (array)
- Section objects must include:
  - section_id (integer), title (string), intent (string), scenes (array)
- Scene objects must include:
  - scene_id (integer), summary (string), type (string), outcome (string), characters (array of character_id strings)
- Preserve required transition contract and link fields from phase 04/05:
  - location_start_label/location_end_label
  - location_start_id/location_end_id (optional in model output; orchestrator compiles canonical ids from labels)
  - location_start/location_end
  - handoff_mode/constraint_state
  - transition_in_text/transition_in_anchors
  - transition_out_text/transition_out_anchors/consumes_outcome_from/hands_off_to (chapter_id:scene_id)
  - seam_score/seam_resolution
  - inserted_by_pipeline/purpose on pipeline-inserted scenes
- transition_in_text/transition_in_anchors must exist on EVERY scene (including first scenes in chapter).
- transition_out_text/transition_out_anchors and hands_off_to must exist on every non-last scene in chapter, including section-final scenes when chapter continues.
- Strict hard-cut rule:
  - In strict transition mode, hard_cut is disallowed and must be converted to a non-hard-cut handoff mode.
  - Do not emit handoff_mode=hard_cut in strict mode.
- Preserve section.end_condition for every section.
- Preserve section closure anchors (end_condition_echo on section-final scenes).
- Do NOT emit placeholder location/transition values (current_location, unknown, placeholder, tbd, here, there).
- Maintain reference-integrity for all character/thread ids.
- Thread and character references are case-sensitive and must match top-level registry ids exactly.
- Because strict validation rejects placeholder tokens, do not use bare tokens `here` or `there` in transition text fields; use concrete location nouns instead.
- Do not emit alternate key names for required schema fields.

Thread policy:
- Target multiple touches per thread (default target >=3 is warning-oriented unless strict mode is configured).
- Prefer escalation over repeated identical beat.

Bridge policy:
- chapter.bridge.to_next should be reflected in next chapter opening intent/scene.
- Prefer minimal edits that keep existing structure.

Use scene-count policy:
{{scene_count_policy}}

If you cannot satisfy constraints after correction attempts, return error_v1:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "error_type": "validation_error",
  "reason_code": "thread_payoff_refinement_blocked",
  "missing_fields": ["chapters[0].sections[0].scenes[0].transition_out_text"],
  "phase": "phase_06_thread_payoff_refinement",
  "action_hint": "Preserve transition/link contract and repair missing thread/callback integrity."
}

Cast-refined outline (phase 05):
{{outline_cast_refined_v1_1}}

Book:
{{book}}

Targets:
{{targets}}

User prompt (optional):
{{user_prompt}}

Notes:
{{notes}}

Transition hints (optional):
{{transition_hints}}
