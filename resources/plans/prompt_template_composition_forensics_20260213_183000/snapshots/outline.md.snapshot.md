# Snapshot: outline.md

- Source: `resources/prompt_templates/outline.md`
- SHA256: `5CC31E096D85313344F8030EEF1CBC5CA2539EAE7AD5625E9FF0A3FE31452848`
- Line count: `157`
- Byte length: `4747`

```text
   1: # OUTLINE
   2: 
   3: You are the outline planner. Create a compact outline for the book.
   4: Return ONLY a single JSON object that matches the outline schema v1.1.
   5: No markdown, no code fences, no commentary.
   6: Keep summaries concise but in the author voice from the system prompt.
   7: 
   8: Core contract: each SCENE is one scene to be written (scene == writing unit).
   9: Scenes must vary per chapter. Do NOT use a fixed scene count.
  10: 
  11: Sections are required:
  12: - Every chapter must include a sections array.
  13: - Typical chapters should have 3-8 sections (target).
  14: - A simple/interlude chapter may use 2-4 sections (rare).
  15: - Each section usually has 2-6 scenes.
  16: - A 1-scene section is allowed only for a stinger/hook moment.
  17: - Total scenes per chapter should naturally land in 6-32, varying by complexity.
  18: 
  19: Scene quality rules:
  20: - Each scene must include type and outcome.
  21: - outcome must be a concrete state change.
  22: - Do not pad with travel/recap/mood-only scenes.
  23: If a user prompt is provided, treat it as grounding context. Integrate its details, but keep the schema and scene rules.
  24: 
  25: 
  26: Chapter role vocabulary (prefer one):
  27: - hook, setup, pressure, reversal, revelation, investigation, journey, trial, alliance, betrayal, siege, confrontation, climax, aftermath, transition, hinge
  28: If it truly does not fit, use the closest role; custom roles are allowed but should be 1-2 words.
  29: 
  30: Scene type vocabulary (prefer one):
  31: - setup, action, reveal, escalation, choice, consequence, aftermath, transition
  32: If it truly does not fit, use the closest type; custom types are allowed but should be 1-2 words.
  33: 
  34: Tempo values (prefer one):
  35: - slow_burn, steady, rush
  36: If it truly does not fit, use the closest tempo; custom values are allowed but should be 1-2 words.
  37: 
  38: Required top-level keys:
  39: - schema_version ("1.1")
  40: - chapters (array)
  41: 
  42: Optional top-level keys (recommended):
  43: - threads (array of thread stubs)
  44: - characters (array of character stubs)
  45: 
  46: Each chapter must include:
  47: - chapter_id
  48: - title
  49: - goal
  50: - chapter_role
  51: - stakes_shift
  52: - bridge (object with from_prev, to_next)
  53: - pacing (object with intensity, tempo, expected_scene_count; expected_scene_count is a soft target)
  54: - sections (array)
  55: 
  56: Each section must include:
  57: - section_id
  58: - title
  59: - intent
  60: - scenes (array of scene objects)
  61: 
  62: Optional section keys:
  63: - section_role
  64: 
  65: Each scene must include:
  66: - scene_id
  67: - summary
  68: - type
  69: - outcome
  70: - characters (array of character_id values present in the scene)
  71: 
  72: Optional scene keys:
  73: - introduces (array of character_id values introduced in the scene)
  74: - threads (array of thread_id values touched in the scene)
  75: - callbacks (array of ids: character/thread/lore references)
  76: 
  77: Character stub format:
  78: {
  79:   "character_id": "CHAR_<slug>",
  80:   "name": "",
  81:   "pronouns": "",
  82:   "role": "",
  83:   "intro": {"chapter": 1, "scene": 1}
  84: }
  85: 
  86: Thread stub format:
  87: {
  88:   "thread_id": "THREAD_<slug>",
  89:   "label": "",
  90:   "status": "open"
  91: }
  92: 
  93: Output ordering guidance:
  94: - Write chapters first. After chapters, list threads and characters at the end of the JSON object.
  95: 
  96: JSON shape example (fill with real values):
  97: {
  98:   "schema_version": "1.1",
  99:   "chapters": [
 100:     {
 101:       "chapter_id": 1,
 102:       "title": "",
 103:       "goal": "",
 104:       "chapter_role": "hook",
 105:       "stakes_shift": "",
 106:       "bridge": {"from_prev": "", "to_next": ""},
 107:       "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 10},
 108:       "sections": [
 109:         {
 110:           "section_id": 1,
 111:           "title": "",
 112:           "intent": "",
 113:           "scenes": [
 114:             {"scene_id": 1, "summary": "", "type": "setup", "outcome": "", "characters": ["CHAR_new_character_name"], "introduces": ["CHAR_new_character_name"]}
 115:           ]
 116:         }
 117:       ]
 118:     },
 119:     {
 120:       "chapter_id": 2,
 121:       "title": "",
 122:       "goal": "",
 123:       "chapter_role": "setup",
 124:       "stakes_shift": "",
 125:       "bridge": {"from_prev": "", "to_next": ""},
 126:       "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 8},
 127:       "sections": [
 128:         {
 129:           "section_id": 1,
 130:           "title": "",
 131:           "intent": "",
 132:           "scenes": [
 133:             {"scene_id": 1, "summary": "", "type": "transition", "outcome": "", "characters": ["CHAR_new_character_name"]}
 134:           ]
 135:         }
 136:       ]
 137:     }
 138:   ],
 139:   "threads": [
 140:     {"thread_id": "THREAD_prophecy", "label": "The Awakened Sage", "status": "open"}
 141:   ],
 142:   "characters": [
 143:     {"character_id": "CHAR_new_character_name", "name": "New Character", "pronouns": "they/them", "role": "protagonist", "intro": {"chapter": 1, "scene": 1}}
 144:   ]
 145: }
 146: 
 147: Book:
 148: {{book}}
 149: 
 150: Targets:
 151: {{targets}}
 152: 
 153: User prompt (optional, may be empty):
 154: {{user_prompt}}
 155: 
 156: Notes:
 157: {{notes}}
```
