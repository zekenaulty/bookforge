# OUTLINE PIPELINE PHASE 05: CAST FUNCTION REFINEMENT

Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.

Return ONLY a single JSON object. No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Required output schema:
{
  "schema_version": "cast_refine_v1",
  "outline": {
    "schema_version": "1.1",
    "chapters": []
  },
  "cast_report": {
    "core_character_ids": [],
    "supporting_character_ids": [],
    "episodic_character_ids": [],
    "recurring_without_job_count": 0,
    "edits_applied": []
  }
}

Goal:
- Ensure recurring characters have clear causal jobs.
- Enforce introduction integrity.
- Reduce cast bloat by merge/demotion instead of inflation.

Rules:
- Preserve chapter/section/scene ordering unless correction is required.
- Preserve phase-04 transition requirements:
  - location_start/location_end
  - handoff_mode/constraint_state
  - transition_in_text/transition_in_anchors
  - consumes_outcome_from/hands_off_to/transition_out link obligations
  - seam_score/seam_resolution
- Keep link format chapter_id:scene_id.
- Preserve section closure anchors (end_condition_echo).
- Preserve registry integrity for characters/threads when referenced.
- A recurring character should appear in >=3 scenes unless explicitly justified in edits_applied.
- A recurring character must cause at least one concrete scene outcome.

If you cannot satisfy constraints after correction attempts, return error_v1:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "phase": "phase_05_cast_function_refinement",
  "reasons": ["..."],
  "validator_evidence": [{"code": "validation_code", "message": "...", "path": "json.path", "scene_ref": "chapter:scene"}],
  "retryable": false
}

Transition-refined outline (phase 04):
{{outline_transitions_refined_v1_1}}

Book:
{{book}}

Targets:
{{targets}}

Notes:
{{notes}}
