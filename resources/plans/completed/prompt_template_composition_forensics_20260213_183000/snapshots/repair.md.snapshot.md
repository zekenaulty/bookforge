# Snapshot: repair.md

- Source: `resources/prompt_templates/repair.md`
- SHA256: `57605D83A5197268F33334B45C9E09118994CAD25F4AE3690C14D10F7C44EE72`
- Line count: `257`
- Byte length: `18703`

```text
   1: # REPAIR
   2: 
   3: Fix the scene based on lint issues.
   4: Summaries are reference-only; do not recap them in prose unless scene_card explicitly requires recap.
   5: Timeline Lock: only depict events explicitly listed in the current Scene Card. Do not depict, imply, or resolve later-scene milestones (acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
   6: State primacy: pre-scene invariants and summary facts are binding unless the Scene Card depicts a change. If this scene changes a durable fact, update must_stay_true to the final end-of-scene value and remove the old entry.
   7: Milestone uniqueness: if a milestone is marked DONE in must_stay_true, do not depict it again. If marked NOT_YET, do not depict it now.
   8: - must_stay_true reconciliation (mandatory):
   9:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  10:   - Remove conflicting old invariants rather than preserving them.
  11: - must_stay_true removal (mandatory when a durable fact is superseded):
  12:   - Add "REMOVE: <exact prior invariant text>" in summary_update.must_stay_true.
  13:   - Place REMOVE lines before the new final invariant.
  14:   - REMOVE lines also apply to key_facts_ring (purge stale facts from continuity).
  15: Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
  16: Inventory contract: track ownership and container location for key items; update must_stay_true when items move or change hands.
  17: - Inventory posture reconciliation:
  18:   - If inventory/containers change (held/stowed/container), must_stay_true must be updated to the final posture.
  19:   - Add REMOVE lines for prior inventory/container invariants before the new final entries.
  20:   - Use canonical invariant formats:
  21:     - inventory: CHAR_X -> <item display_name> (status=held|carried|equipped|stowed, container=hand_left|hand_right|<container>)
  22:     - container: <container> (owner=CHAR_X, contents=[<item display_name>, ...])
  23: For held items, specify container=hand_left or container=hand_right.
  24: Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates.
  25: Durable vs ephemeral mechanics:
  26: - If a DURABLE mechanic appears multiple times in the scene (e.g., base values then final values), the LAST occurrence is canonical.
  27: - You MUST capture the canonical end-of-scene values in character_continuity_system_updates.
  28: - When allocation/level-up happens, update all affected point pools (e.g., stat_points, skill_points, perk_points) if shown.
  29: - Do not treat early UI snapshots as canonical if the scene later corrects them.
  30: - DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
  31: - EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
  32: - UI gate: only include bracketed UI blocks when scene_card.ui_allowed=true. If false, remove or rephrase UI blocks into narrative prose.
  33: - UI/system readouts must be on their own line, starting with '[' and ending with ']'.
  34: - Do NOT embed bracketed UI in narrative sentences.
  35: - Allowed suffix after a UI block is punctuation or a short parenthetical annotation (e.g., (locked), (Warning: ...)).
  36: 
  37: - DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
  38: - EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene.
  39: Canonical descriptors (colors, item names, effect IDs, mechanic labels) must be reused exactly; do not paraphrase.
  40: If item_registry or plot_devices are provided, they are canonical durable-state references for authoritative labels and custody terms.
  41: Use item_registry.items[].display_name in prose; use item_id only in patches/JSON. The display_name must be human readable and not an escaped id/name.
  42: Appearance contract:
  43: - Attire boundary: wearables are inventory-owned. Do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
  44: - appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change.
  45: - Durable appearance changes must be declared in scene_card.durable_appearance_changes (or an explicit appearance milestone) and recorded via appearance_updates.
  46: - If a durable appearance change occurs in this scene, record it in character_updates.appearance_updates with a reason.
  47: - APPEARANCE_CHECK is required in COMPLIANCE for each cast_present_id (4-8 tokens from atoms/marks).
  48: 
  49: Naming repairs:
  50: - If lint flags an item naming issue, fix it with minimal edits.
  51: - Do not remove humor; simply anchor the item (add display_name near first mention) and ensure custody-change sentences include the display_name.
  52: - Do not rename item_id or registry fields; only adjust prose wording.
  53: summary_update arrays are mandatory; do not omit or leave empty unless explicitly stated.
  54: STATE_PATCH must record all major events and outcomes from the prose; if an event happens, add it to key_events and update must_stay_true as needed.
  55: - must_stay_true reconciliation (mandatory):
  56: 
  57:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  58:   - Remove conflicting old invariants rather than preserving them.
  59: must_stay_true must include a milestone ledger entry for every milestone referenced in the Scene Card or already present in state.
  60: - must_stay_true reconciliation (mandatory):
  61: 
  62:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  63:   - Remove conflicting old invariants rather than preserving them.
  64: If state lacks a key invariant needed for this scene, seed it in must_stay_true using standard phrasing.
  65: - must_stay_true reconciliation (mandatory):
  66: 
  67:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  68:   - Remove conflicting old invariants rather than preserving them.
  69: Enforce scene-card durable constraints: `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`; treat `required_visible_on_page` as explicit narrative requirement when present.
  70: Respect `timeline_scope` and `ontological_scope`.
  71: - Scope override rule (non-present / non-real scenes):
  72:   - If timeline_scope != "present" OR ontological_scope != "real", do NOT emit durable mutation blocks UNLESS they are required for this scene transition (based on scene_card + current state).
  73:   - Durable mutation blocks include: inventory_alignment_updates, transfer_updates, item_registry_updates, plot_device_updates, and any other durable-state mutation you emit.
  74:   - If they are required for the story (e.g., items must persist into the next real scene, required_in_custody/required_scene_accessible lists them, or transition_type implies continuity of physical possessions), you MUST set scope_override=true (or allow_non_present_mutation=true) on EACH affected update object and set reason_category="timeline_override".
  75: Return corrected prose plus a corrected state_patch JSON block.
  76: 
  77: Output format (required, no code fences, no commentary):
  78: COMPLIANCE:
  79: Scene ID: <scene_card.scene_id>
  80: Allowed events: <short list from Scene Card>
  81: Forbidden milestones: <from must_stay_true>
  82: - must_stay_true reconciliation (mandatory):
  83: 
  84:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  85:   - Remove conflicting old invariants rather than preserving them.
  86: Current arm-side / inventory facts: <from must_stay_true>
  87: - must_stay_true reconciliation (mandatory):
  88: 
  89:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
  90:   - Remove conflicting old invariants rather than preserving them.
  91: 
  92: APPEARANCE_CHECK:
  93: - CHAR_ID: <4-8 tokens from atoms/marks>
  94: 
  95: PROSE:
  96: <scene prose>
  97: 
  98: STATE_PATCH:
  99: <json>
 100: 
 101: STATE_PATCH rules:
 102: - Use schema_version "1.0".
 103: - Use world_updates to update world state (cast_present, location, recent_facts, open_threads).
 104: - Use scene_card.cast_present_ids for cast_present (ids, not names).
 105: - Use scene_card.thread_ids for open_threads (thread ids).
 106: - Do not invent new character or thread ids.
 107: - Include summary_update arrays: last_scene (array of 2-4 sentence strings), key_events (array of 3-7 bullet strings), must_stay_true (array of 3-7 bullet strings), chapter_so_far_add (array of bullet strings).
 108: - must_stay_true reconciliation (mandatory):
 109: 
 110:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
 111:   - Remove conflicting old invariants rather than preserving them.
 112: - Include story_so_far_add only at chapter end (or when scene_card explicitly requests).
 113: - Use threads_touched only if you can reference thread ids from scene_card.thread_ids.
 114: - Include character_continuity_system_updates for cast_present_ids when mechanics change.
 115:   - Use set/delta/remove/reason.
 116:   - Use nested families under set/delta (examples): stats, skills, titles, resources, effects, statuses, classes, ranks.
 117:   - titles must be arrays of objects with stable name fields (example: [{"name": "Novice", "source": "starting_class", "active": true}]).
 118:   - If a new mechanic family appears, add it under set with a stable key.
 119: - Include global_continuity_system_updates only if global mechanics change.
 120: - global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
 121:   - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
 122:   - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
 123: - All *_updates arrays must contain objects; never emit bare strings as array entries.
 124: - JSON shape guardrails (strict, do not deviate):
 125:   - character_updates MUST be an array of objects.
 126:     - INVALID: "character_updates": {"character_id": "CHAR_X"}
 127:     - VALID: "character_updates": [{"character_id": "CHAR_X"}]
 128:   - character_continuity_system_updates MUST be an array of objects with character_id.
 129:     - INVALID: "character_continuity_system_updates": {"set": {...}}
 130:     - VALID: "character_continuity_system_updates": [{"character_id": "CHAR_X", "set": {...}}]
 131:   - summary_update fields must be arrays of strings.
 132:     - INVALID: "summary_update": {"last_scene": "text"}
 133:     - VALID: "summary_update": {"last_scene": ["text"], "key_events": ["..."], "must_stay_true": ["..."], "chapter_so_far_add": ["..."]}
 134: - must_stay_true reconciliation (mandatory):
 135: 
 136:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
 137:   - Remove conflicting old invariants rather than preserving them.
 138:   - appearance_updates MUST be an object under character_updates.
 139:     - INVALID: "appearance_updates": [{"set": {...}}] OR "appearance_updates": {"marks_add": [...]}
 140:     - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
 141: - character_updates.containers must be an array of objects with at least: container, owner, contents (array).
 142: - Durable-state mutation blocks are mandatory when applicable:
 143: - Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
 144:   - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
 145:     - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
 146:     - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
 147:   - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
 148:     - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
 149:     - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]
 150: 
 151:   - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
 152:   - custodian must be a non-null string id/scope (character id or "world"). Never use null.
 153:     - INVALID: "custodian": null
 154:     - VALID: "custodian": "CHAR_ARTIE" or "world"
 155:   - owner_scope must be "character" or "world" and must match the custodian scope.
 156:   - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
 157:   - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.
 158: - Transfer vs registry conflict rule (must follow):
 159:   - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
 160:   - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
 161:   - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).  - `inventory_alignment_updates` for scene-fit posture normalization.
 162:   - `item_registry_updates` for durable item metadata/custody changes.
 163:   - `plot_device_updates` for durable plot-device custody/activation changes.
 164:   - `transfer_updates` for item handoffs (source, destination, reason, optional transfer_chain).
 165:   - Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
 166:   - `inventory_alignment_updates` must be an array of objects; never an object with an `updates` field.
 167:   - inventory_alignment_updates[*].set MUST be an object (not a list).
 168:     - INVALID: "set": []
 169:     - VALID:   "set": {"inventory": [...], "containers": [...]}
 170: - For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
 171: - If you mutate durable state, do not leave the same mutation only in prose.
 172: - Include character_updates entries for cast_present_ids that change state (inventory, containers, persona shifts).
 173: - appearance_updates: when a durable appearance change happens, include appearance_updates on the relevant character_updates entry.
 174:   - appearance_updates MUST be an object, not an array.
 175:     - INVALID: "appearance_updates": [{"set": {...}, "reason": "..."}]
 176:     - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
 177:   - appearance_updates.set may include atoms and marks only (canonical truth).
 178:     - Do NOT put marks_add at the top level; it belongs under set.
 179:     - Use set.marks_add / set.marks_remove for marks changes.
 180:     - Use set.atoms for atom changes.
 181:   - appearance_updates.reason is required (brief, factual).
 182:   - Do NOT set summary or art text in appearance_updates (derived after acceptance)
 183:   - Each entry must include character_id, chapter, scene, inventory (full current list), containers (full current list), invariants_add (array), persona_updates (array).
 184:   - character_updates.inventory MUST be an array of objects, never string item ids.
 185:   - Inventory object shape: {"item": "ITEM_or_name", "container": "hand_left|hand_right|<container>", "status": "held|carried|equipped|stowed"}.
 186:   - Container object shape: {"container": "<name>", "owner": "CHAR_id", "contents": ["ITEM_id", "..."]}.
 187:   - If you have a single persona update, still wrap it in an array of strings.
 188: - must_stay_true must include a milestone ledger and invariants using standard phrasing, e.g.:
 189: - must_stay_true reconciliation (mandatory):
 190: 
 191:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
 192:   - Remove conflicting old invariants rather than preserving them.
 193:   - Avoid numeric mechanics in must_stay_true; store them in continuity system updates instead.
 194: - must_stay_true reconciliation (mandatory):
 195: 
 196:   - If you change a durable value in the patch, you must update must_stay_true to match the end-of-scene value.
 197:   - Remove conflicting old invariants rather than preserving them.
 198:   - inventory: CHAR_example -> shard (carried, container=satchel)
 199:   - inventory: CHAR_example -> longsword (carried, container=hand_right)
 200:   - container: satchel (owner=CHAR_example, contents=[shard, maps])
 201:   - milestone: shard_bind = DONE/NOT_YET
 202:   - milestone: maps_acquired = DONE/NOT_YET
 203:   - injury: right forearm scar / left arm filament
 204:   - ownership: shard (carried) / shard (bound but physical)
 205: 
 206: Issues:
 207: {{issues}}
 208: 
 209: Scene card:
 210: {{scene_card}}
 211: 
 212: Character registry (id -> name):
 213: {{character_registry}}
 214: 
 215: Thread registry:
 216: {{thread_registry}}
 217: 
 218: Character states (per cast_present_ids):
 219: {{character_states}}
 220: 
 221: Scene:
 222: {{prose}}
 223: 
 224: State:
 225: {{state}}
 226: 
 227: Item registry (canonical):
 228: {{item_registry}}
 229: 
 230: Plot devices (canonical):
 231: {{plot_devices}}
 232: 
 233: JSON Contract Block (strict; arrays only):
 234: - All *_updates must be arrays of objects, even when there is only one update.
 235: - INVALID vs VALID examples:
 236:   - item_registry_updates:
 237:     - INVALID: "item_registry_updates": {"set": {"ITEM_X": {...}}}
 238:     - VALID:   "item_registry_updates": [{"item_id": "ITEM_X", "set": {...}}]
 239:   - plot_device_updates:
 240:     - INVALID: "plot_device_updates": {"set": {"DEVICE_X": {...}}}
 241:     - VALID:   "plot_device_updates": [{"device_id": "DEVICE_X", "set": {...}}]
 242:   - transfer_updates:
 243:     - INVALID: "transfer_updates": {"item_id": "ITEM_X"}
 244:     - VALID:   "transfer_updates": [{"item_id": "ITEM_X", "reason": "handoff"}]
 245:   - inventory_alignment_updates:
 246:     - INVALID: "inventory_alignment_updates": {"updates": [{...}]}
 247:     - VALID:   "inventory_alignment_updates": [{"character_id": "CHAR_X", "set": {...}, "reason": "..."}]
 248:   - global_continuity_system_updates:
 249:     - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
 250:     - VALID:   "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
 251: - custodian must be a non-null string id or "world"; never null.
 252: 
 253: 
 254: 
 255: 
 256: 
 257: 
```
