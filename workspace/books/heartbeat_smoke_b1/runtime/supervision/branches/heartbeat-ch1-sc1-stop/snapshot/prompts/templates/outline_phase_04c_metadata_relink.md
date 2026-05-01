# OUTLINE PIPELINE PHASE 04C: METADATA RELINK (WINDOW-SCOPED)

Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.

Return ONLY a single JSON object. No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Required output schema:
{
  "schema_version": "outline_relink_v1",
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
    "updated_character_ids": [],
    "notes": []
  }
}

Goal:
- Reconcile structural metadata drift caused by inserted scenes.
- Operate only within the specified impact window.
- Do NOT rewrite prose or invent new semantic content.

Window context (authoritative):
{{phase_04c_window_json}}

Allowed edit fields (authoritative):
{{phase_04c_allowed_fields_json}}

Hard rules:
- Output MUST contain exactly one chapter in outline.chapters.
- The output chapter_id MUST match chapter_target_id.
- Do not echo the full book.
- Do not add/remove scenes or change scene order.
- Do not change scene_id values.
- Only modify scenes listed in the window scene_refs.
- Only modify fields listed in allowed fields; all other fields must remain unchanged.
- Do not alter transition_in/out text or anchors unless explicitly allowed.
- Do not add/remove characters in the registry.
- Only update character intro metadata for the allowed character ids and only when it mismatches the earliest appearance.
- If you edit handoff_mode, it must be one of:
  direct_continuation, escorted_transfer, detained_then_release, time_skip, hard_cut, montage,
  offscreen_processing, combat_disengage, arrival_checkpoint, aftermath_relocation, terminal.
- Do not use seam resolution values (inline_bridge, micro_scene, full_scene) in handoff_mode.

Reporting:
- phase_report.window_id must match the window_id provided in the window context.
- phase_report.touched_scene_refs should list scenes you edited.
- phase_report.touched_fields should list fields you edited.
- phase_report.updated_character_ids should list characters whose intro metadata changed.

If you cannot satisfy constraints after correction attempts, return error_v1:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "error_type": "validation_error",
  "reason_code": "phase04c_relink_failed",
  "missing_fields": ["phase_report.touched_scene_refs"],
  "phase": "phase_04c_metadata_relink",
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
