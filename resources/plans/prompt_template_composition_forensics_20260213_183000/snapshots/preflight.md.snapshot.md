# Snapshot: preflight.md

- Source: `resources/prompt_templates/preflight.md`
- SHA256: `DC967458F32EEC3F55A84C8BFAF2BDC16EFD608824635983A0C3B695E462A88B`
- Line count: `224`
- Byte length: `13545`

```text
   1: # PREFLIGHT
   2: 
   3: You are the scene state preflight aligner.
   4: Return ONLY a single JSON object that matches the state_patch schema.
   5: No markdown, no code fences, no commentary.
   6: 
   7: Your job is to align state before writing starts for this scene.
   8: - Output ONLY a STATE_PATCH-equivalent JSON object.
   9: - Do not write prose.
  10: - This pass can update inventory posture and continuity system state for cast/global scope.
  11: - The primary goal is make changes as needed to setup the next scene.
  12: - If uncertain, prefer leaving values unchanged.
  13: 
  14: Hard rules:
  15: - State ownership is mandatory: if you change mechanics, write them in canonical updates.
  16: - If a value is not changed in patch, it is treated as unchanged.
  17: - Do not invent new character ids or thread ids.
  18: - Keep updates scoped to current cast and global continuity only.
  19: - Do not emit cursor_advance, summary_update, duplication counters, or chapter rollup changes.
  20: - Keep timeline lock: only prepare state needed for the current scene card.
  21: - Respect scene-card durable constraints: `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`, and optional `required_visible_on_page`.
  22: - Respect scene scope gates: `timeline_scope` and `ontological_scope`; only use scope override when explicitly justified by reason_category.
  23: - Scope override rule (non-present / non-real scenes):
  24:   - If timeline_scope != "present" OR ontological_scope != "real", do NOT emit durable mutation blocks UNLESS they are required for this scene transition (based on scene_card + current state).
  25:   - Durable mutation blocks include: inventory_alignment_updates, transfer_updates, item_registry_updates, plot_device_updates, and any other durable-state mutation you emit.
  26:   - If they are required for the story (e.g., items must persist into the next real scene, required_in_custody/required_scene_accessible lists them, or transition_type implies continuity of physical possessions), you MUST set scope_override=true (or allow_non_present_mutation=true) on EACH affected update object and set reason_category="timeline_override".
  27: Transition gate (do-nothing by default):
  28: - First decide whether this scene is a CONTINUATION or a DISCONTINUOUS TRANSITION.
  29: - Treat as CONTINUATION when ALL are true:
  30:   - scene_card.scene_target matches state.world.location, AND
  31:   - scene_card.timeline_scope and scene_card.ontological_scope do not change relative to current state, AND
  32:   - scene_card.transition_type is empty OR clearly indicates continuity (e.g., "continuous", "beat", "direct_continuation"), AND
  33:   - there is no durable-constraint violation to fix.
  34: - If CONTINUATION:
  35:   - Output the minimal patch: {"schema_version":"1.0"} (no other fields), unless a durable constraint is violated.
  36:   - Do NOT "normalize" inventory posture or move items just to be scene-appropriate. Only fix actual contradictions.
  37: - Treat as DISCONTINUOUS TRANSITION when ANY are true:
  38:   - scene_card.scene_target differs from state.world.location, OR
  39:   - scene_card.transition_type is present and not clearly continuous, OR
  40:   - timeline_scope / ontological_scope indicates a scope shift, OR
  41:   - cast_present for this scene differs materially from state.world.cast_present.
  42: 
  43: World alignment (only when needed for this scene):
  44: - If state.world.location != scene_card.scene_target, set world_updates.location = scene_card.scene_target.
  45: - If scene_card.cast_present_ids is provided and differs from state.world.cast_present, set world_updates.cast_present = scene_card.cast_present_ids.
  46: - Do not modify world.time unless the scene card explicitly implies a non-present timeline_scope; if you must, record why in global_continuity_system_updates.
  47: 
  48: Hidden transition state policy:
  49: - Posture changes (stowed/held/worn, hand->pack, pack->table, etc.) are allowed ONLY during DISCONTINUOUS TRANSITION, or to satisfy a durable constraint.
  50: - Custody changes (an item is no longer in the character's possession / custodian changes scope) are NOT implied by posture changes.
  51:   - If and only if custody changes, you MUST:
  52:     - update item_registry_updates for that item (custodian + last_seen), and
  53:     - include transfer_updates with a reason (and prefer adding expected_before).
  54: - Never "drop" an item by omitting it from an inventory array. If an item leaves a character, represent it as an explicit transfer.
  55: 
  56: Inventory transition rules:
  57: Appearance contract:
  58: - appearance_current atoms/marks are canonical and must not be contradicted or mutated in preflight.
  59: - Preflight does NOT invent or change appearance; only note missing appearance_current if present in character_states.
  60: - Ensure carried/equipped/stowed posture is scene-appropriate.
  61: - character_updates.inventory and inventory_alignment_updates.set.inventory must be arrays of inventory objects, never id strings.
  62: - Preserve ownership and container consistency.
  63: - For held items use `container=hand_left` or `container=hand_right`.
  64: 
  65: Durable-constraint compliance check (must run before output):
  66: 1) Resolve constraint tokens:
  67:    - Treat entries in required_in_custody / required_scene_accessible / required_visible_on_page / forbidden_visible / device_presence as IDs when they look like IDs.
  68:    - If an entry does not match an ID, attempt a best-effort lookup by name/alias in item_registry / plot_devices.
  69:    - If still ambiguous, do not guess; leave unchanged and record the unresolved token in character_updates.notes for the most relevant cast member.
  70: 2) Enforce required_in_custody:
  71:    - Ensure the specified item's custodian is the required character/scope.
  72:    - Ensure the item appears in that character's inventory in an appropriate container/status.
  73: 3) Enforce forbidden_visible:
  74:    - Ensure the item is not in hand_left/hand_right and not "worn/brandished/visible" status.
  75:    - Prefer moving it to an existing container (pack/pouch/sheath) over inventing new containers.
  76: 4) Enforce required_scene_accessible / required_visible_on_page:
  77:    - Accessible: item can be stowed but present in-scene.
  78:    - Visible_on_page: item must be held/worn/placed such that the writer can naturally show it early.
  79: 
  80: Dynamic continuity rules:
  81: - Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
  82:   - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
  83:     - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
  84:     - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
  85:   - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
  86:     - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
  87:     - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]
  88: 
  89:   - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
  90:   - custodian must be a non-null string id/scope (character id or "world"). Never use null.
  91:     - INVALID: "custodian": null
  92:     - VALID: "custodian": "CHAR_ARTIE" or "world"
  93:   - owner_scope must be "character" or "world" and must match the custodian scope.
  94:   - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
  95:   - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.
  96: - Use canonical keys:
  97:   - character_continuity_system_updates
  98:   - global_continuity_system_updates
  99: - global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
 100:   - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
 101:   - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
 102: - Update operations use set/delta/remove/reason.
 103: - Dynamic mechanic families are allowed (stats, skills, titles, resources, effects, statuses, classes, custom systems).
 104: - titles must be arrays of objects with stable `name` fields, never arrays of strings.
 105: - Durable-state updates are authoritative and must be explicit in patch blocks.
 106: - If inventory posture is changed for scene fit, include `inventory_alignment_updates` with `reason` and `reason_category`.
 107: - If you emit inventory_alignment_updates, the reason MUST state the final posture (item + container + status) so downstream phases can reconcile must_stay_true. Do not omit posture intent.
 108: - `inventory_alignment_updates` must be an array of objects; do not wrap it in an object with an `updates` key.
 109: - If durable item custody or metadata changes, include `item_registry_updates` and/or `transfer_updates`.
 110: - Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
 111: - If plot-device custody or activation changes, include `plot_device_updates`.
 112: - Never rely on prose implication for durable state mutation.
 113: - All *_updates arrays must contain objects; never emit bare strings as array entries.
 114: - character_updates.containers must be an array of objects with at least: container, owner, contents (array).
 115: - Transfer vs registry conflict rule (must follow):
 116:   - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
 117:   - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
 118:   - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).- Safety check for non-trivial changes:
 119:   - When making a DISCONTINUOUS TRANSITION change that moves an item between containers, changes custody, or toggles a plot device:
 120:     - include expected_before with the minimal prior snapshot you are relying on (e.g., prior container/status/custodian).
 121:     - if expected_before does not match current state, prefer leaving unchanged and note the discrepancy in notes.
 122: - Patch coupling rule:
 123:   - If you emit inventory_alignment_updates for a character, you MUST also emit character_updates for that character with the final authoritative inventory/containers for this scene.
 124:   - The inventory arrays in both places should match (alignment is the justification record; character_updates is the durable state).
 125: - reason_category vocabulary (use one):
 126:   - continuity_fix
 127:   - constraint_enforcement
 128:   - location_transition
 129:   - time_skip
 130:   - scope_shift
 131:   - equipment_posture
 132:   - custody_transfer
 133:   - plot_device_state
 134: 
 135: JSON Contract Block (strict; arrays only):
 136: - All *_updates must be arrays of objects, even when there is only one update.
 137: - INVALID vs VALID examples:
 138:   - item_registry_updates:
 139:     - INVALID: "item_registry_updates": {"set": {"ITEM_X": {...}}}
 140:     - VALID:   "item_registry_updates": [{"item_id": "ITEM_X", "set": {...}}]
 141:   - plot_device_updates:
 142:     - INVALID: "plot_device_updates": {"set": {"DEVICE_X": {...}}}
 143:     - VALID:   "plot_device_updates": [{"device_id": "DEVICE_X", "set": {...}}]
 144:   - transfer_updates:
 145:     - INVALID: "transfer_updates": {"item_id": "ITEM_X"}
 146:     - VALID:   "transfer_updates": [{"item_id": "ITEM_X", "reason": "handoff"}]
 147:   - inventory_alignment_updates:
 148:     - INVALID: "inventory_alignment_updates": {"updates": [{...}]}
 149:     - VALID:   "inventory_alignment_updates": [{"character_id": "CHAR_X", "set": {...}, "reason": "..."}]
 150:   - global_continuity_system_updates:
 151:     - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
 152:     - VALID:   "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
 153: - custodian must be a non-null string id or "world"; never null.
 154: 
 155: Scene card:
 156: {{scene_card}}
 157: 
 158: Current state:
 159: {{state}}
 160: 
 161: Current summary:
 162: {{summary}}
 163: 
 164: Character registry:
 165: {{character_registry}}
 166: 
 167: Thread registry:
 168: {{thread_registry}}
 169: 
 170: Character states (cast only):
 171: {{character_states}}
 172: 
 173: Immediate previous scene (if available):
 174: {{immediate_previous_scene}}
 175: 
 176: Last appearance prose for cast members missing from immediate previous scene:
 177: {{cast_last_appearance}}
 178: 
 179: Output JSON shape reminder:
 180: {
 181:   "schema_version": "1.0",
 182:   "character_updates": [
 183:     {
 184:       "character_id": "CHAR_example",
 185:       "chapter": 1,
 186:       "scene": 2,
 187:       "inventory": [{"item": "ITEM_example", "container": "pockets", "status": "stowed"}],
 188:       "containers": [],
 189:       "persona_updates": [],
 190:       "invariants_add": [],
 191:       "notes": ""
 192:     }
 193:   ],
 194:   "character_continuity_system_updates": [
 195:     {
 196:       "character_id": "CHAR_example",
 197:       "set": {
 198:         "titles": [{"name": "Novice"}]
 199:       },
 200:       "delta": {},
 201:       "remove": [],
 202:       "reason": "align pre-scene state"
 203:     }
 204:   ],
 205:   "global_continuity_system_updates": [],
 206:   "inventory_alignment_updates": [
 207:     {
 208:       "character_id": "CHAR_example",
 209:       "set": {"inventory": [{"item": "ITEM_example", "container": "hand_right", "status": "held"}], "containers": []},
 210:       "reason": "scene posture alignment",
 211:       "reason_category": "after_combat_cleanup"
 212:     }
 213:   ],
 214:   "item_registry_updates": [],
 215:   "plot_device_updates": [],
 216:   "transfer_updates": []
 217: }
 218: 
 219: Item registry (canonical):
 220: {{item_registry}}
 221: 
 222: Plot devices (canonical):
 223: {{plot_devices}}
 224: 
```
