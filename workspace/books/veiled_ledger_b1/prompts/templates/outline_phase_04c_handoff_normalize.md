# OUTLINE PIPELINE PHASE 04C-HANDOFF: HANDOFF NORMALIZE (CHAPTER-SCOPED)

Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.

Return ONLY a single JSON object. No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Required output schema:
{
  "schema_version": "outline_handoff_normalize_v1",
  "outline": {
    "schema_version": "1.1",
    "chapters": [
      {
        "chapter_id": 1
      }
    ]
  },
  "phase_report": {
    "touched_scene_refs": [],
    "notes": []
  }
}

Goal:
- Normalize handoff_mode for chapter-final scenes and for location-jump scenes.
- Do NOT rewrite prose or change scene ordering.

Handoff fixes to apply (authoritative list of scene refs + reasons):
{{phase_04c_handoff_fix_json}}

Important:
- The `scene_ref` field is the ONLY scene you may edit for that fix.
- `from_scene_ref` is context only; never edit it.

Allowed location-jump handoff modes:
{{phase_04c_handoff_allowed_jump_modes_json}}

Hard rules:
- Output MUST contain exactly one chapter in outline.chapters.
- The output chapter_id MUST match chapter_target_id.
- Do not echo the full book.
- Do not add/remove scenes or change scene order.
- Do not change scene_id values.
- Only modify handoff_mode for the listed scene refs.
- Do not infer or fix additional scene refs beyond the list.
- Do not change hands_off_to or consumes_outcome_from.

If you cannot satisfy constraints after correction attempts, return error_v1:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "error_type": "validation_error",
  "reason_code": "phase04c_handoff_normalize_failed",
  "missing_fields": ["phase_report.touched_scene_refs"],
  "phase": "phase_04c_handoff_normalize",
  "action_hint": "Only update handoff_mode for listed scenes; keep all other fields unchanged."
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
