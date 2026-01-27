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
- Containers are tracked separately in containers[] with owner and contents.

Invariant phrasing (use exact strings where possible):
- inventory: <CHAR_ID> -> <item> (status=carried|stowed|equipped, container=<container_label>)
- container: <container_label> (owner=<CHAR_ID>, contents=[item1, item2])
- injury: <character_id> <injury/location>

Book:
{{book}}

Outline characters:
{{outline_characters}}

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
      "inventory": [
        {"item": "longsword", "status": "carried", "container": "hand_right"}
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
