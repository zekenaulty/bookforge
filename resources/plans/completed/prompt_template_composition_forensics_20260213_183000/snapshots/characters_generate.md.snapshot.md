# Snapshot: characters_generate.md

- Source: `resources/prompt_templates/characters_generate.md`
- SHA256: `2F2EBE29BFBB7CBE823ED38BF2714E853B0C5FA41F65E47D3CD0217B4A97E85D`
- Line count: `139`
- Byte length: `5221`

```text
   1: # CHARACTERS GENERATE
   2: 
   3: You are refining outline character stubs into canon character entries and initial per-book character state.
   4: Return ONLY a single JSON object. No markdown, no code fences, no commentary.
   5: Do not invent new characters; expand only the outline-provided stubs.
   6: 
   7: Required top-level keys:
   8: - schema_version ("1.0")
   9: - characters (array)
  10: 
  11: Each character object must include:
  12: - character_id
  13: - name
  14: - pronouns
  15: - role
  16: - persona (object)
  17: - inventory (array)
  18: - containers (array)
  19: - invariants (array of strings)
  20: - appearance_base (object)
  21: 
  22: Recommended mechanic seed key (dynamic):
  23: - character_continuity_system_state (object)
  24:   - Include any starting mechanics known at setup time.
  25:   - Examples: stats, skills, titles, classes, ranks, resources, cooldowns, effects, statuses.
  26:   - titles must be an array of objects (not strings).
  27:   - You may add future mechanic families if relevant.
  28:   - Use dynamic continuity families as needed: stats, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, system_tracking_metadata, extended_system_data.
  29:   - For LitRPG-like systems, prefer structured stats/skills/titles in character_continuity_system_state.
  30: 
  31: Appearance guidance (durable, canonical):
  32: - appearance_base is the canon self-image for this character.
  33: - Include: summary, atoms, marks, alias_map.
  34: - Atoms are normalized traits (species, sex_presentation, age_band, height_band, build, hair_color, hair_style, eye_color, skin_tone).
  35: - marks are durable identifiers (scars, tattoos, prosthetics). No temporary grime or wounds.
  36: - alias_map lists acceptable synonyms for lint tolerance (e.g., hair_color: ["dark brown"]).
  37: - appearance_current will be derived from appearance_base for the book unless explicitly overridden later.
  38: 
  39: Naming and durable item guidance:
  40: - For items, use a human-readable item_name; do not use ITEM_* ids in prose strings.
  41: - Reserve ITEM_* ids for canonical JSON only; do not use them in prose strings.
  42: - If you emit an item_id here, include item_name as a human label.
  43: 
  44: Starting scene alignment (important):
  45: - The initial inventory/containers/state must prepare each character for the book's first scene.
  46: - Use the Book + Outline characters in THIS prompt as your source of truth for the opening situation.
  47: - If the opening situation is unclear, default to a neutral, plausible posture (hands free, items stowed).
  48: - Example: office/briefing -> no weapons held; battle opener -> weapon may be in hand; travel -> stowed gear.
  49: 
  50: Persona guidance (compact, factual):
  51: - core_traits (array)
  52: - motivations (array)
  53: - fears (array)
  54: - values (array)
  55: - voice_notes (array)
  56: - arc_hint (string)
  57: 
  58: Inventory rules:
  59: - Every carried/held item must include a container location.
  60: - Use explicit container labels (satchel, belt, pack, hand_left, hand_right, sheath, etc.).
  61: - If an item is held, container must be hand_left or hand_right.
  62: - If you use item_id, include item_name (human label) on the same inventory entry. The item_name must be human readable and not an escaped id value.
  63: - Prefer item_name in prose-facing fields; item_id only in canonical JSON.
  64: - Containers are tracked separately in containers[] with owner and contents.
  65: 
  66: Invariant phrasing (use exact strings where possible):
  67: - inventory: <CHAR_ID> -> <item> (status=carried|stowed|equipped, container=<container_label>)
  68: - container: <container_label> (owner=<CHAR_ID>, contents=[item1, item2])
  69: - injury: <character_id> <injury/location>
  70: 
  71: Book:
  72: {{book}}
  73: 
  74: Outline characters:
  75: {{outline_characters}}
  76: 
  77: Outline opening context (chapter/section/scene 1):
  78: {{outline_opening}}
  79: 
  80: Series info (if any):
  81: {{series}}
  82: 
  83: Output JSON:
  84: {
  85:   "schema_version": "1.0",
  86:   "characters": [
  87:     {
  88:       "character_id": "CHAR_example",
  89:       "name": "",
  90:       "pronouns": "",
  91:       "role": "",
  92:       "persona": {
  93:         "core_traits": [],
  94:         "motivations": [],
  95:         "fears": [],
  96:         "values": [],
  97:         "voice_notes": [],
  98:         "arc_hint": ""
  99:       },
 100:       "appearance_base": {
 101:         "summary": "",
 102:         "atoms": {
 103:           "species": "human",
 104:           "sex_presentation": "",
 105:           "age_band": "",
 106:           "height_band": "",
 107:           "build": "",
 108:           "hair_color": "",
 109:           "hair_style": "",
 110:           "eye_color": "",
 111:           "skin_tone": ""
 112:         },
 113:         "marks": [
 114:           {"name": "", "location": "", "durability": "durable"}
 115:         ],
 116:         "alias_map": {
 117:           "hair_color": [""],
 118:           "eye_color": [""]
 119:         }
 120:       },
 121:       "character_continuity_system_state": {
 122:         "stats": {"hp": {"current": 10, "max": 10}},
 123:         "skills": {"sword": 1},
 124:         "titles": [{"name": "Novice", "source": "starting_class", "active": true}],
 125:         "resources": {"mana": {"current": 5, "max": 5}}
 126:       },
 127:       "inventory": [
 128:         {"item_id": "ITEM_longsword", "item_name": "Longsword", "status": "carried", "container": "hand_right"}
 129:       ],
 130:       "containers": [
 131:         {"container": "satchel", "owner": "CHAR_example", "location": "shoulder_left", "contents": ["maps"]}
 132:       ],
 133:       "invariants": [
 134:         "inventory: CHAR_example -> longsword (status=carried, container=hand_right)",
 135:         "container: satchel (owner=CHAR_example, contents=[maps])"
 136:       ]
 137:     }
 138:   ]
 139: }
```
