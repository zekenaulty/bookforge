# OUTLINE PIPELINE PHASE 05: CAST FUNCTION REFINEMENT (CHAPTER-SCOPED)

Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.

Return ONLY a single JSON object. No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Required output schema:
{
  "schema_version": "cast_refine_v1",
  "outline": {
    "schema_version": "1.1",
    "chapters": [
      {
        "chapter_id": 1
      }
    ]
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
- Ensure recurring characters in this chapter have clear causal jobs.
- Enforce introduction integrity in this chapter.
- Reduce cast bloat by merge/demotion instead of inflation.

Chapter-scoped hard rules:
- Output MUST contain exactly one chapter in outline.chapters.
- The output chapter_id MUST match chapter_target_id.
- Do not echo the full book.

Rules:
- Preserve chapter section/scene ordering unless correction is required.
- Preserve outline schema-required keys and types for chapter/section/scene objects.
- Preserve phase-04 transition requirements:
  - location_start_label/location_end_label
  - location_start_id/location_end_id (optional in model output; orchestrator compiles canonical ids from labels)
  - location_start/location_end
  - handoff_mode/constraint_state
  - transition_in_text/transition_in_anchors
  - consumes_outcome_from/hands_off_to/transition_out_text/transition_out_anchors link obligations
  - seam_score/seam_resolution
  - inserted_by_pipeline/purpose on pipeline-inserted scenes
- Preserve section.end_condition and section closure anchors (end_condition_echo).
- Keep link format chapter_id:scene_id.
- Do NOT emit placeholder location/transition values (current_location, unknown, placeholder, tbd, here, there).
- Preserve registry integrity for characters/threads when referenced.

If you cannot satisfy constraints after correction attempts, return error_v1:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "error_type": "validation_error",
  "reason_code": "cast_refinement_blocked",
  "missing_fields": ["outline.characters"],
  "phase": "phase_05_cast_function_refinement",
  "action_hint": "Preserve transition contract and supply required cast registry fields."
}

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

Notes:
{{notes}}
