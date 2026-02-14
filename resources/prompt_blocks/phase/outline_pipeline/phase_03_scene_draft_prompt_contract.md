# OUTLINE PIPELINE PHASE 03: SCENE DRAFT

You are generating the first full outline draft.
Return ONLY a single JSON object that matches outline schema v1.1.
No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Core contract:
- Each scene is one writing unit.
- Every scene must include type and outcome.
- outcome must be a concrete state change.
- Do not pad with travel/recap/mood-only scenes.

Required top-level keys:
- schema_version ("1.1")
- chapters (array)

Recommended top-level keys:
- threads (array)
- characters (array)

Chapter requirements:
- chapter_id, title, goal, chapter_role, stakes_shift, bridge, pacing, sections.

Section requirements:
- section_id, title, intent, scenes.

Scene requirements:
- scene_id, summary, type, outcome, characters.

Optional scene keys:
- introduces, threads, callbacks
- transition_in, transition_out, edge_intent, consumes_outcome_from, hands_off_to

Rules:
- Preserve chapter/section structure from prior phases.
- scene counts should align with section target_scene_count (soft).
- Introduces must be first appearance only (no duplicates).
- Characters and threads referenced in scenes must exist in top-level arrays.
- Keep ids stable and deterministic.

JSON shape example:
{
  "schema_version": "1.1",
  "chapters": [
    {
      "chapter_id": 1,
      "title": "",
      "goal": "",
      "chapter_role": "hook",
      "stakes_shift": "",
      "bridge": {"from_prev": "", "to_next": ""},
      "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 10},
      "sections": [
        {
          "section_id": 1,
          "title": "",
          "intent": "",
          "scenes": [
            {
              "scene_id": 1,
              "summary": "",
              "type": "setup",
              "outcome": "",
              "characters": ["CHAR_example"],
              "introduces": ["CHAR_example"],
              "threads": ["THREAD_example"],
              "callbacks": [],
              "transition_in": "",
              "transition_out": "",
              "edge_intent": "",
              "consumes_outcome_from": "",
              "hands_off_to": "SC_001_002"
            }
          ]
        }
      ]
    }
  ],
  "threads": [
    {"thread_id": "THREAD_example", "label": "", "status": "open"}
  ],
  "characters": [
    {"character_id": "CHAR_example", "name": "", "pronouns": "", "role": "", "intro": {"chapter": 1, "scene": 1}}
  ]
}

Outline spine (phase 01):
{{outline_spine_v1}}

Section architecture (phase 02):
{{outline_sections_v1}}

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

