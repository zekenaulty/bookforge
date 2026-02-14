# OUTLINE PIPELINE PHASE 02: SECTION ARCHITECTURE

You are generating section architecture from the chapter spine.
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
          "target_scene_count": 3
        }
      ]
    }
  ]
}

Rules:
- Include every chapter_id from outline_spine_v1.
- section_id must be unique within each chapter.
- Typical section count per chapter is 3-8.
- Interlude/transition chapters may use 2-4 sections.
- target_scene_count should usually be 2-6.
- section intent must describe a pressure/question that resolves by section end.
- section intents in a chapter must be distinct and progressive.
- Do not change chapter goals/bridges from phase 01.

Validation intent:
- The next phase will generate scenes from these section intents.
- Keep section intents concrete and action-driving.

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

