# Snapshot: write.md

- Source: `resources/prompt_templates/write.md`
- SHA256: `898B8FCFA1997DE8C7BCDF0636E462EA52064D627E2257C3DF644725443888F4`
- Line count: `237`
- Byte length: `18254`

```text
   1: # WRITE
   2: Write the scene described by the scene card.
   3: - YOU MUST ALWAYS RETURN PROSE AND THE STATE_PATCH.
   4: - Start in motion. No recap.
   5: - Summaries are reference-only; do not recap them in prose unless scene_card explicitly requires recap.
   6: - Use the continuity pack and state for continuity.
   7: - Use character_registry to keep names consistent in prose.
   8: - Timeline Lock: only depict events explicitly listed in the current Scene Card. Do not depict, imply, or resolve later-scene milestones (acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
   9: - State primacy: pre-scene invariants and summary facts are binding unless the Scene Card depicts a change. If this scene changes a durable fact, update must_stay_true to the final end-of-scene value and remove the old entry.
  10: - Milestone uniqueness: if a milestone is marked DONE in must_stay_true, do not depict it again. If marked NOT_YET, do not depict it now.
  11: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  12: - must_stay_true removal (mandatory when a durable fact is superseded):
  13:   - Add "REMOVE: <exact prior invariant text>" in summary_update.must_stay_true.
  14:   - Place REMOVE lines before the new final invariant.
  15:   - REMOVE lines also apply to key_facts_ring (purge stale facts from continuity).
  16: - Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
  17: - Inventory contract: track ownership and container location for key items; update must_stay_true when items move or change hands.
  18: - Inventory posture reconciliation:
  19:   - If inventory/containers change (held/stowed/container), must_stay_true must be updated to the final posture.
  20:   - Add REMOVE lines for prior inventory/container invariants before the new final entries.
  21:   - Use canonical invariant formats:
  22:     - inventory: CHAR_X -> <item display_name> (status=held|carried|equipped|stowed, container=hand_left|hand_right|<container>)
  23:     - container: <container> (owner=CHAR_X, contents=[<item display_name>, ...])
  24: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  25: 
  26: - For held items, specify container=hand_left or container=hand_right.
  27: - Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates.
  28: Durable vs ephemeral mechanics:
  29: - If a DURABLE mechanic appears multiple times in the scene (e.g., base values then final values), the LAST occurrence is canonical.
  30: - You MUST capture the canonical end-of-scene values in character_continuity_system_updates.
  31: - When allocation/level-up happens, update all affected point pools (e.g., stat_points, skill_points, perk_points) if shown.
  32: - Do not treat early UI snapshots as canonical if the scene later corrects them.
  33: - DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
  34: - EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
  35: - UI gate: only include bracketed UI blocks when scene_card.ui_allowed=true. If false, do not include UI blocks; rephrase into narrative prose.
  36: - UI/system readouts must be on their own line, starting with '[' and ending with ']'.
  37: - Do NOT embed bracketed UI in narrative sentences.
  38: - Allowed suffix after a UI block is punctuation or a short parenthetical annotation (e.g., (locked), (Warning: ...)).
  39: 
  40: - DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
  41: - EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene.
  42: - titles are arrays of objects with stable name fields; do not emit titles as plain strings.
  43: - If item_registry or plot_devices are provided, they are canonical durable-state references for ownership/custody labels in authoritative outputs.
  44: - Use item_registry.items[].display_name in prose; use item_id only in patches/JSON. The display_name must be human readable and not an escaped id/name.
  45: Appearance contract:
  46: - Attire boundary: wearables are inventory-owned. Do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
  47: - appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change.
  48: - Durable appearance changes must be declared in scene_card.durable_appearance_changes (or an explicit appearance milestone) and recorded via appearance_updates.
  49: - If a durable appearance change occurs in this scene, record it in character_updates.appearance_updates with a reason.
  50: - APPEARANCE_CHECK is required in COMPLIANCE for each cast_present_id (4-8 tokens from atoms/marks).
  51: 
  52: Durable item naming discipline:
  53: - When you first describe a durable item, anchor it by using the canonical display_name within the same paragraph (or within the next 2 sentences).
  54: - After anchoring, you may use brief descriptors for style if unambiguous.
  55: - During any custody/handling change, include the canonical display_name in that sentence.
  56: - If a required event is not in the Scene Card, do not perform it.
  57: - Enforce scene-card durable constraints: honor `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, and `device_presence`; treat `required_visible_on_page` as explicit narrative requirement when present.
  58: - Respect `timeline_scope` and `ontological_scope` when proposing durable mutations; do not mutate physical custody in non-present/non-real scope unless explicitly marked override.
  59: - Scope override rule (non-present / non-real scenes):
  60:   - If timeline_scope != "present" OR ontological_scope != "real", do NOT emit durable mutation blocks UNLESS they are required for this scene transition (based on scene_card + current state).
  61:   - Durable mutation blocks include: inventory_alignment_updates, transfer_updates, item_registry_updates, plot_device_updates, and any other durable-state mutation you emit.
  62:   - If they are required for the story (e.g., items must persist into the next real scene, required_in_custody/required_scene_accessible lists them, or transition_type implies continuity of physical possessions), you MUST set scope_override=true (or allow_non_present_mutation=true) on EACH affected update object and set reason_category="timeline_override".
  63: - summary_update arrays are mandatory; do not omit or leave empty unless explicitly stated.
  64: - STATE_PATCH must record all major events and outcomes from the prose; if an event happens, add it to key_events and update must_stay_true as needed.
  65: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  66: 
  67: - must_stay_true must include a milestone ledger entry for every milestone referenced in the Scene Card or already present in state.
  68: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  69: 
  70: - If state lacks a key invariant needed for this scene, seed it in must_stay_true using standard phrasing.
  71: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  72: 
  73: - Return prose plus a state_patch JSON block.
  74: STATE_PATCH rules:
  75: - Use schema_version "1.0".
  76: - Use world_updates to update world state (cast_present, location, recent_facts, open_threads).
  77: - Use scene_card.cast_present_ids for cast_present (ids, not names).
  78: - Use scene_card.thread_ids for open_threads (thread ids).
  79: - Do not invent new character or thread ids.
  80: - Include summary_update arrays: last_scene (array of 2-4 sentence strings), key_events (array of 3-7 bullet strings), must_stay_true (array of 3-7 bullet strings), chapter_so_far_add (array of bullet strings).
  81: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
  82: 
  83: - Include story_so_far_add only at chapter end (or when scene_card explicitly requests).
  84: - Use threads_touched only if you can reference thread ids from scene_card.thread_ids.
  85: - Include character_continuity_system_updates for cast_present_ids when mechanics change.
  86:   - Use set/delta/remove/reason.
  87:   - Use nested families under set/delta (examples): stats, skills, titles, resources, effects, statuses, classes, ranks.
  88:   - titles must be arrays of objects with stable name fields (example: [{"name": "Novice", "source": "starting_class", "active": true}]).
  89:   - If a new mechanic family appears, add it under set with a stable key.
  90: - Include global_continuity_system_updates only if global mechanics change.
  91: - global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
  92:   - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
  93:   - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
  94: - All *_updates arrays must contain objects; never emit bare strings as array entries.
  95: - JSON shape guardrails (strict, do not deviate):
  96:   - character_updates MUST be an array of objects.
  97:     - INVALID: "character_updates": {"character_id": "CHAR_X"}
  98:     - VALID: "character_updates": [{"character_id": "CHAR_X"}]
  99:   - character_continuity_system_updates MUST be an array of objects with character_id.
 100:     - INVALID: "character_continuity_system_updates": {"set": {...}}
 101:     - VALID: "character_continuity_system_updates": [{"character_id": "CHAR_X", "set": {...}}]
 102:   - summary_update fields must be arrays of strings.
 103:     - INVALID: "summary_update": {"last_scene": "text"}
 104:     - VALID: "summary_update": {"last_scene": ["text"], "key_events": ["..."], "must_stay_true": ["..."], "chapter_so_far_add": ["..."]}
 105: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
 106: 
 107:   - appearance_updates MUST be an object under character_updates.
 108:     - INVALID: "appearance_updates": [{"set": {...}}] OR "appearance_updates": {"marks_add": [...]}
 109:     - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
 110: - character_updates.containers must be an array of objects with at least: container, owner, contents (array).
 111: - Durable-state mutation blocks are mandatory when applicable:
 112: - Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
 113:   - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
 114:     - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
 115:     - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
 116:   - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
 117:     - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
 118:     - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]
 119: 
 120:   - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
 121:   - custodian must be a non-null string id/scope (character id or "world"). Never use null.
 122:     - INVALID: "custodian": null
 123:     - VALID: "custodian": "CHAR_ARTIE" or "world"
 124:   - owner_scope must be "character" or "world" and must match the custodian scope.
 125:   - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
 126:   - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.
 127: - Transfer vs registry conflict rule (must follow):
 128:   - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
 129:   - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
 130:   - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).  - `inventory_alignment_updates` for scene-fit posture normalization.
 131:   - `item_registry_updates` for durable item metadata/custody changes.
 132:   - `plot_device_updates` for durable plot-device custody/activation changes.
 133:   - `transfer_updates` for item handoffs (source, destination, reason, optional transfer_chain).
 134:   - Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
 135:   - `inventory_alignment_updates` must be an array of objects; never an object with an `updates` field.
 136: - For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
 137: - If you mutate durable state, do not leave the same mutation only in prose.
 138: - Include character_updates entries for cast_present_ids that change state (inventory, containers, persona shifts).
 139: - appearance_updates: when a durable appearance change happens, include appearance_updates on the relevant character_updates entry.
 140:   - appearance_updates MUST be an object, not an array.
 141:     - INVALID: "appearance_updates": [{"set": {...}, "reason": "..."}]
 142:     - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
 143:   - appearance_updates.set may include atoms and marks only (canonical truth).
 144:     - Do NOT put marks_add at the top level; it belongs under set.
 145:     - Use set.marks_add / set.marks_remove for marks changes.
 146:     - Use set.atoms for atom changes.
 147:   - appearance_updates.reason is required (brief, factual).
 148:   - Do NOT set summary or art text in appearance_updates (derived after acceptance)
 149:   - Each entry must include character_id, chapter, scene, inventory (full current list), containers (full current list), invariants_add (array), persona_updates (array).
 150:   - character_updates.inventory MUST be an array of objects, never string item ids.
 151:   - Inventory object shape: {"item": "ITEM_or_name", "container": "hand_left|hand_right|<container>", "status": "held|carried|equipped|stowed"}.
 152:   - Container object shape: {"container": "<name>", "owner": "CHAR_id", "contents": ["ITEM_id", "..."]}.
 153:   - If you have a single persona update, still wrap it in an array of strings.
 154: - must_stay_true must include a milestone ledger and invariants using standard phrasing, e.g.:
 155: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
 156: 
 157:   - Avoid numeric mechanics in must_stay_true; store them in continuity system updates instead.
 158: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
 159: 
 160:   - inventory: CHAR_example -> shard (carried, container=satchel)
 161:   - inventory: CHAR_example -> longsword (carried, container=hand_right)
 162:   - container: satchel (owner=CHAR_example, contents=[shard, maps])
 163:   - milestone: shard_bind = DONE/NOT_YET
 164:   - milestone: maps_acquired = DONE/NOT_YET
 165:   - injury: right forearm scar / left arm filament
 166:   - ownership: shard (carried) / shard (bound but physical)
 167: 
 168: Scene card:
 169: {{scene_card}}
 170: 
 171: Continuity pack:
 172: {{continuity_pack}}
 173: 
 174: Character registry (id -> name):
 175: {{character_registry}}
 176: 
 177: Thread registry:
 178: {{thread_registry}}
 179: 
 180: Character states (per cast_present_ids):
 181: {{character_states}}
 182: 
 183: Style anchor:
 184: {{style_anchor}}
 185: 
 186: State:
 187: {{state}}
 188: 
 189: Output (required, no code fences):
 190: COMPLIANCE:
 191: Scene ID: <scene_card.scene_id>
 192: Allowed events: <short list from Scene Card>
 193: Forbidden milestones: <from must_stay_true>
 194: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
 195: 
 196: Current arm-side / inventory facts: <from must_stay_true>
 197: - must_stay_true is end-of-scene truth only (last occurrence wins); do not keep earlier values that are superseded by the scene.
 198: 
 199: Durable changes committed: <final durable values to record in continuity updates>
 200: 
 201: APPEARANCE_CHECK:
 202: - CHAR_ID: <4-8 tokens from atoms/marks>
 203: 
 204: PROSE:
 205: <scene prose>
 206: STATE_PATCH:
 207: <json>
 208: 
 209: Item registry (canonical):
 210: {{item_registry}}
 211: 
 212: Plot devices (canonical):
 213: {{plot_devices}}
 214: 
 215: JSON Contract Block (strict; arrays only):
 216: - All *_updates must be arrays of objects, even when there is only one update.
 217: - INVALID vs VALID examples:
 218:   - item_registry_updates:
 219:     - INVALID: "item_registry_updates": {"set": {"ITEM_X": {...}}}
 220:     - VALID:   "item_registry_updates": [{"item_id": "ITEM_X", "set": {...}}]
 221:   - plot_device_updates:
 222:     - INVALID: "plot_device_updates": {"set": {"DEVICE_X": {...}}}
 223:     - VALID:   "plot_device_updates": [{"device_id": "DEVICE_X", "set": {...}}]
 224:   - transfer_updates:
 225:     - INVALID: "transfer_updates": {"item_id": "ITEM_X"}
 226:     - VALID:   "transfer_updates": [{"item_id": "ITEM_X", "reason": "handoff"}]
 227:   - inventory_alignment_updates:
 228:     - INVALID: "inventory_alignment_updates": {"updates": [{...}]}
 229:     - VALID:   "inventory_alignment_updates": [{"character_id": "CHAR_X", "set": {...}, "reason": "..."}]
 230:   - global_continuity_system_updates:
 231:     - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
 232:     - VALID:   "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
 233: - custodian must be a non-null string id or "world"; never null.
 234: 
 235: 
 236: 
 237: 
```
