# OUTLINE

You are the outline planner. Create a compact outline for the book.
Return ONLY a single JSON object that matches the outline schema.
No markdown, no code fences, no commentary.
Keep summaries concise but in the author voice from the system prompt.

Beats must vary per chapter. Do NOT use a fixed beat count.
Use enough beats per chapter to support multiple scenes (aim 6-32, vary by chapter complexity).

Required top-level keys:
- schema_version ("1.0")
- chapters (array)

Optional top-level keys (recommended):
- characters (array of character stubs with ids and first appearance)

Each chapter must include:
- chapter_id
- title
- goal
- beats (array of objects with beat_id and summary; entry_state/exit_state optional)

Each beat should include:
- beat_id
- summary
- characters (array of character_id values present in the beat)
- introduces (array of character_id values introduced in the beat; optional)

Character stub format:
{
  "character_id": "CHAR_<slug>",
  "name": "",
  "pronouns": "",
  "role": "",
  "intro": {"chapter": 1, "beat": 1}
}

JSON shape example (fill with real values):
{
  "schema_version": "1.0",
  "characters": [
    {"character_id": "CHAR_kaelen", "name": "Kaelen", "pronouns": "he/him", "role": "protagonist", "intro": {"chapter": 1, "beat": 1}}
  ],
  "chapters": [
    {
      "chapter_id": 1,
      "title": "",
      "goal": "",
      "beats": [
        {"beat_id": 1, "summary": "", "characters": ["CHAR_kaelen"], "introduces": ["CHAR_kaelen"]}
      ]
    }
  ]
}

Book:
{{book}}

Targets:
{{targets}}

Notes:
{{notes}}
