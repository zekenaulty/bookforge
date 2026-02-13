<!-- begin entry=E001 semantic=outline.prompt_contract_and_outline_schema source=resources/prompt_blocks/phase/outline/prompt_contract_and_outline_schema.md repeat=1/1 -->
# OUTLINE

You are the outline planner. Create a compact outline for the book.
Return ONLY a single JSON object that matches the outline schema v1.1.
No markdown, no code fences, no commentary.
Keep summaries concise but in the author voice from the system prompt.

Core contract: each SCENE is one scene to be written (scene == writing unit).
Scenes must vary per chapter. Do NOT use a fixed scene count.

Sections are required:
- Every chapter must include a sections array.
- Typical chapters should have 3-8 sections (target).
- A simple/interlude chapter may use 2-4 sections (rare).
- Each section usually has 2-6 scenes.
- A 1-scene section is allowed only for a stinger/hook moment.
- Total scenes per chapter should naturally land in 6-32, varying by complexity.

Scene quality rules:
- Each scene must include type and outcome.
- outcome must be a concrete state change.
- Do not pad with travel/recap/mood-only scenes.
If a user prompt is provided, treat it as grounding context. Integrate its details, but keep the schema and scene rules.


Chapter role vocabulary (prefer one):
- hook, setup, pressure, reversal, revelation, investigation, journey, trial, alliance, betrayal, siege, confrontation, climax, aftermath, transition, hinge
If it truly does not fit, use the closest role; custom roles are allowed but should be 1-2 words.

Scene type vocabulary (prefer one):
- setup, action, reveal, escalation, choice, consequence, aftermath, transition
If it truly does not fit, use the closest type; custom types are allowed but should be 1-2 words.

Tempo values (prefer one):
- slow_burn, steady, rush
If it truly does not fit, use the closest tempo; custom values are allowed but should be 1-2 words.

Required top-level keys:
- schema_version ("1.1")
- chapters (array)

Optional top-level keys (recommended):
- threads (array of thread stubs)
- characters (array of character stubs)

Each chapter must include:
- chapter_id
- title
- goal
- chapter_role
- stakes_shift
- bridge (object with from_prev, to_next)
- pacing (object with intensity, tempo, expected_scene_count; expected_scene_count is a soft target)
- sections (array)

Each section must include:
- section_id
- title
- intent
- scenes (array of scene objects)

Optional section keys:
- section_role

Each scene must include:
- scene_id
- summary
- type
- outcome
- characters (array of character_id values present in the scene)

Optional scene keys:
- introduces (array of character_id values introduced in the scene)
- threads (array of thread_id values touched in the scene)
- callbacks (array of ids: character/thread/lore references)

Character stub format:
{
  "character_id": "CHAR_<slug>",
  "name": "",
  "pronouns": "",
  "role": "",
  "intro": {"chapter": 1, "scene": 1}
}

Thread stub format:
{
  "thread_id": "THREAD_<slug>",
  "label": "",
  "status": "open"
}

Output ordering guidance:
- Write chapters first. After chapters, list threads and characters at the end of the JSON object.

JSON shape example (fill with real values):
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
            {"scene_id": 1, "summary": "", "type": "setup", "outcome": "", "characters": ["CHAR_new_character_name"], "introduces": ["CHAR_new_character_name"]}
          ]
        }
      ]
    },
    {
      "chapter_id": 2,
      "title": "",
      "goal": "",
      "chapter_role": "setup",
      "stakes_shift": "",
      "bridge": {"from_prev": "", "to_next": ""},
      "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 8},
      "sections": [
        {
          "section_id": 1,
          "title": "",
          "intent": "",
          "scenes": [
            {"scene_id": 1, "summary": "", "type": "transition", "outcome": "", "characters": ["CHAR_new_character_name"]}
          ]
        }
      ]
    }
  ],
  "threads": [
    {"thread_id": "THREAD_prophecy", "label": "The Awakened Sage", "status": "open"}
  ],
  "characters": [
    {"character_id": "CHAR_new_character_name", "name": "New Character", "pronouns": "they/them", "role": "protagonist", "intro": {"chapter": 1, "scene": 1}}
  ]
}

Book:
{{book}}

Targets:
{{targets}}

User prompt (optional, may be empty):
{{user_prompt}}

Notes:
{{notes}}

<!-- end entry=E001 semantic=outline.prompt_contract_and_outline_schema -->
