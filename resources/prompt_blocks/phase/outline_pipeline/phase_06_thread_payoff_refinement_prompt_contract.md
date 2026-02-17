# OUTLINE PIPELINE PHASE 06: THREAD AND PAYOFF REFINEMENT (CHAPTER-SCOPED)

Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.

Return ONLY a single JSON object matching outline schema v1.1.
No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Goal:
- Produce final chapter-level thread/payoff refinement while preserving transition and cast integrity.

Required top-level keys:
- schema_version ("1.1")
- chapters (array with exactly one chapter)

Chapter-scoped hard rules:
- Output MUST contain exactly one chapter in chapters.
- The output chapter_id MUST match chapter_target_id.
- Do not echo the full book.

Required integrity:
- Keep section and scene ordering chapter-local unless correction is required.
- Preserve transition contract and links:
  - location_start_label/location_end_label
  - location_start_id/location_end_id (optional in model output; orchestrator compiles canonical ids from labels)
  - location_start/location_end
  - handoff_mode/constraint_state
  - transition_in_text/transition_in_anchors
  - transition_out_text/transition_out_anchors/consumes_outcome_from/hands_off_to (chapter_id:scene_id)
  - seam_score/seam_resolution
  - inserted_by_pipeline/purpose on pipeline-inserted scenes
- transition_in_text/transition_in_anchors must exist on every scene.
- transition_out_text/transition_out_anchors and hands_off_to must exist on every non-last scene in chapter.
- Strict hard-cut rule:
  - In strict transition mode, hard_cut is disallowed and must be converted to a non-hard-cut handoff mode.
  - Do not emit handoff_mode=hard_cut in strict mode.
- Preserve section.end_condition and section closure anchors (end_condition_echo).
- Do NOT emit placeholder location/transition values (current_location, unknown, placeholder, tbd, here, there).
- Maintain reference integrity for all character/thread ids.

Thread policy:
- Target multiple touches per thread (default target >=3 is warning-oriented unless strict mode is configured).
- Prefer escalation over repeated identical beats.

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

Use scene-count policy:
{{scene_count_policy}}

Chapter target id:
{{chapter_target_id}}

Chapter input outline:
{{chapter_input_outline}}

Previous chapter context (read-only):
{{chapter_prev_outline}}

Next chapter context (read-only):
{{chapter_next_outline}}

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