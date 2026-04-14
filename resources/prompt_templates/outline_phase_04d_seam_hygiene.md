# OUTLINE PIPELINE PHASE 04D: SEAM HYGIENE (WINDOW-SCOPED)

Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.

Return ONLY a single JSON object. No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Required output schema:
{
  "schema_version": "outline_seam_hygiene_v1",
  "outline": {
    "schema_version": "1.1",
    "chapters": [
      {
        "chapter_id": 1
      }
    ]
  },
  "phase_report": {
    "window_id": "",
    "touched_scene_refs": [],
    "touched_fields": [],
    "notes": []
  }
}

Goal:
- Repair seam metadata and transition anchors within the specified window.
- Ensure every scene has seam_score + seam_resolution.
- Fix splice-related anchor drift (successor transition_in_anchors must reflect the true predecessor).

Window context (authoritative):
{{phase_04d_window_json}}

Allowed edit fields (authoritative):
{{phase_04d_allowed_fields_json}}

Hard rules:
- Output MUST contain exactly one chapter in outline.chapters.
- The output chapter_id MUST match chapter_target_id.
- Do not echo the full book.
- Do not add/remove scenes or change scene order.
- Do not change scene_id values.
- Only modify scenes listed in the window scene_refs.
- Only modify fields listed in allowed fields; all other fields must remain unchanged.
- Do not change characters, threads, or registry data.
- If a splice inserted a scene, you must ensure the successor scene's transition_in_* reflects the new predecessor.

Reporting:
- phase_report.window_id must match the window_id provided in the window context.
- phase_report.touched_scene_refs should list scenes you edited.
- phase_report.touched_fields should list fields you edited.

If you cannot satisfy constraints after correction attempts, return error_v1:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "error_type": "validation_error",
  "reason_code": "phase04d_seam_hygiene_failed",
  "missing_fields": ["phase_report.touched_scene_refs"],
  "phase": "phase_04d_seam_hygiene",
  "action_hint": "Only edit allowed fields within the window and keep scene order unchanged."
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
