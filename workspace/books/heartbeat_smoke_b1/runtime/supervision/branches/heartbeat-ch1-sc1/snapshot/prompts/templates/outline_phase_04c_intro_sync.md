# OUTLINE PIPELINE PHASE 04C-INTRO: CHARACTER INTRO SYNC (CHAPTER-SCOPED)

Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.

Return ONLY a single JSON object. No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Required output schema:
{
  "schema_version": "outline_intro_sync_v1",
  "outline": {
    "schema_version": "1.1",
    "chapters": [
      {
        "chapter_id": 1
      }
    ],
    "characters": []
  },
  "phase_report": {
    "updated_character_ids": [],
    "notes": []
  }
}

Goal:
- Align character registry intro metadata to the earliest actual on-page introductions.
- Only update the listed character ids for this chapter.
- Do NOT rewrite scenes or alter scene ordering.

Character ids to validate and correct:
{{phase_04c_intro_character_ids_json}}

Character registry (authoritative for non-intro fields):
{{character_registry}}

Hard rules:
- Output MUST contain exactly one chapter in outline.chapters.
- The output chapter_id MUST match chapter_target_id.
- Do not echo the full book.
- Do not add/remove scenes or change scene order.
- Do not change scene_id values.
- Do not modify any scene fields.
- Only modify characters[*].intro for the listed character ids.
- Do not add/remove characters.

If you cannot satisfy constraints after correction attempts, return error_v1:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "error_type": "validation_error",
  "reason_code": "phase04c_intro_sync_failed",
  "missing_fields": ["phase_report.updated_character_ids"],
  "phase": "phase_04c_intro_sync",
  "action_hint": "Only update intro metadata for the allowed character ids; keep scenes unchanged."
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
