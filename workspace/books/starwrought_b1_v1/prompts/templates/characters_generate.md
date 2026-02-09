# CHARACTERS GENERATE

You are refining outline character stubs into canon character entries and initial per-book character state.
Return ONLY a single JSON object. No markdown, no code fences, no commentary.
Do not invent new characters; expand only the outline-provided stubs.

Required top-level keys:
- schema_version ("1.0")
- characters (array)

Each character object must include:
- character_id
- name
- pronouns
- role
- persona (object)
- inventory (array)
- containers (array)
- invariants (array of strings)

Recommended mechanic seed key (dynamic):
- character_continuity_system_state (object)
  - Include any starting mechanics known at setup time.
  - Examples: stats, skills, titles, classes, ranks, resources, cooldowns, effects, statuses.
  - titles must be an array of objects (not strings).
  - You may add future mechanic families if relevant.
  - Use dynamic continuity families as needed: stats, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, system_tracking_metadata, extended_system_data.
  - For LitRPG-like systems, prefer structured stats/skills/titles in character_continuity_system_state.

Naming and durable item guidance:
- For items, use a human-readable item_name; do not use ITEM_* ids in prose strings.
- Reserve ITEM_* ids for canonical JSON only; do not use them in prose strings.
- If you emit an item_id here, include item_name as a human label.
Starting scene alignment (important):
- The initial inventory/containers/state must prepare each character for the book's first scene.
- Use the Book + Outline characters in THIS prompt as your source of truth for the opening situation.
- If the opening situation is unclear, default to a neutral, plausible posture (hands free, items stowed).
- Example: office/briefing -> no weapons held; battle opener -> weapon may be in hand; travel -> stowed gear.

Persona guidance (compact, factual):
- core_traits (array)
- motivations (array)
- fears (array)
- values (array)
- voice_notes (array)
- arc_hint (string)

Inventory rules:
- Every carried/held item must include a container location.
- Use explicit container labels (satchel, belt, pack, hand_left, hand_right, sheath, etc.).
- If an item is held, container must be hand_left or hand_right.
- If you use item_id, include item_name (human label) on the same inventory entry. The item_name must be human readable and not an escaped id value.
- Prefer item_name in prose-facing fields; item_id only in canonical JSON.
- Containers are tracked separately in containers[] with owner and contents.

Invariant phrasing (use exact strings where possible):
- inventory: <CHAR_ID> -> <item> (status=carried|stowed|equipped, container=<container_label>)
- container: <container_label> (owner=<CHAR_ID>, contents=[item1, item2])
- injury: <character_id> <injury/location>

Book:
{{book}}

Outline characters:
{{outline_characters}}

Outline opening context (chapter/section/scene 1):
{{outline_opening}}

Series info (if any):
{{series}}

Output JSON:
{
  "schema_version": "1.0",
  "characters": [
    {
      "character_id": "CHAR_example",
      "name": "",
      "pronouns": "",
      "role": "",
      "persona": {
        "core_traits": [],
        "motivations": [],
        "fears": [],
        "values": [],
        "voice_notes": [],
        "arc_hint": ""
      },
      "character_continuity_system_state": {
        "stats": {"hp": {"current": 10, "max": 10}},
        "skills": {"sword": 1},
        "titles": [{"name": "Novice", "source": "starting_class", "active": true}],
        "resources": {"mana": {"current": 5, "max": 5}}
      },
      "inventory": [
        {"item_id": "ITEM_longsword", "item_name": "Longsword", "status": "carried", "container": "hand_right"}
      ],
      "containers": [
        {"container": "satchel", "owner": "CHAR_example", "location": "shoulder_left", "contents": ["maps"]}
      ],
      "invariants": [
        "inventory: CHAR_example -> longsword (status=carried, container=hand_right)",
        "container: satchel (owner=CHAR_example, contents=[maps])"
      ]
    }
  ]
}


