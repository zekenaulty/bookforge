# OUTLINE PIPELINE PHASE 02: SECTION ARCHITECTURE

Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.

Return ONLY a single JSON object. No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Goal:
- Define chapter-internal mini-arcs before scene listing.
- Do NOT emit scenes in this phase.

Required output schema:
{
  "schema_version": "sections_v1",
  "chapters": [
    {
      "chapter_id": 1,
      "sections": [
        {
          "section_id": 1,
          "title": "",
          "intent": "",
          "section_role": "setup",
          "target_scene_count": 3,
          "end_condition": ""
        }
      ]
    }
  ]
}

Rules:
- Include every chapter_id from outline_spine_v1.
- section_id must be sequential integers within each chapter starting at 1.
- Typical section count per chapter is 3-8; interlude/transition chapters may use 2-4.
- target_scene_count should usually be 2-6.
- section intents must be distinct and progressive.
- end_condition is required and must define deterministic section closure target.
- The section-final scene in phase 03 must echo end_condition exactly via end_condition_echo.
- Keep chapter goals/bridges unchanged from phase 01.
- Sum of section target_scene_count should approximately align with chapter expected_scene_count.

If you cannot satisfy constraints after correction attempts, return error_v1:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "phase": "phase_02_section_architecture",
  "reasons": ["..."],
  "validator_evidence": [{"code": "validation_code", "message": "...", "path": "json.path"}],
  "retryable": false
}

Outline spine (phase 01):
{{outline_spine_v1}}

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
