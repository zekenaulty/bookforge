# Snapshot: state_repair.md

- Source: `resources/prompt_templates/state_repair.md`
- SHA256: `CDCA594405F79DFE7791B54BD94EC48EECF01036E22870DD0A29B27D509CE68D`
- Line count: `189`
- Byte length: `13505`

```text
   1: # STATE REPAIR
   2: 
   3: You are the state repair step. You must output a corrected STATE_PATCH JSON only.
   4: No prose, no commentary, no code fences.
   5: 
   6: Goal:
   7: - Ensure state_patch fully and accurately captures the scene's events and outcomes.
   8: - Fill missing summary_update data and fix invalid formats from draft_patch.
   9: - Preserve pre-scene invariants unless this scene changes them; when it does, update must_stay_true to the final end-of-scene value.
  10: - must_stay_true reconciliation (mandatory):
  11:   - If this scene changes a durable fact (stats/HP/status/title/custody), you MUST update must_stay_true to reflect the final end-of-scene value.
  12:   - Remove or replace any prior must_stay_true entries that conflict with new durable values.
  13:   - Do NOT carry forward conflicting legacy invariants once the scene updates them.
  14: - must_stay_true removal (mandatory when a durable fact is superseded):
  15:   - Add "REMOVE: <exact prior invariant text>" in summary_update.must_stay_true.
  16:   - Place REMOVE lines before the new final invariant.
  17:   - REMOVE lines also apply to key_facts_ring (purge stale facts from continuity).
  18: - Ensure mechanic/UI ownership in continuity system updates.
  19: 
  20: Rules:
  21: - Output a single JSON object that matches the state_patch schema.
  22: - Use schema_version "1.0".
  23: - Use scene_card.cast_present_ids for world_updates.cast_present.
  24: - Use scene_card.thread_ids for world_updates.open_threads.
  25: - Do not invent new character or thread ids.
  26: - summary_update arrays are required: last_scene (2-4 sentences), key_events (3-7 bullets), must_stay_true (3-7 bullets), chapter_so_far_add (bullets).
  27: - Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates
  28: Durable vs ephemeral mechanics:
  29: - UI gate: only include bracketed UI blocks when scene_card.ui_allowed=true. If false, remove or rephrase UI blocks into narrative prose.
  30: 
  31: - If a DURABLE mechanic appears multiple times in the scene (e.g., base values then final values), the LAST occurrence is canonical.
  32: - You MUST capture the canonical end-of-scene values in character_continuity_system_updates.
  33: - When allocation/level-up happens, update all affected point pools (e.g., stat_points, skill_points, perk_points) if shown.
  34: - Do not treat early UI snapshots as canonical if the scene later corrects them.
  35: - DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
  36: - EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
  37: - DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
  38: - EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene..
  39: - titles are arrays of objects with stable name fields; do not emit titles as plain strings.
  40: - Canonical descriptors (colors, item names, effect IDs, mechanic labels) must be reused exactly; do not paraphrase.
  41: - If item_registry or plot_devices are provided, they are canonical durable-state references for authoritative labels and custody terms.
  42: - Use item_registry.items[].display_name in prose; use item_id only in patches/JSON. The display_name must be human readable and not an escaped id/name.
  43: Appearance contract:
  44: - Attire boundary: wearables are inventory-owned. Do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
  45: - appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change.
  46: - Durable appearance changes must be declared in scene_card.durable_appearance_changes (or an explicit appearance milestone) and recorded via appearance_updates.
  47: - If prose depicts a durable appearance change, include character_updates.appearance_updates with a reason.
  48: - Do NOT set summary or art text in appearance_updates (derived after acceptance).
  49: 
  50: Naming repairs:
  51: - If lint flags an item naming issue, fix it with minimal edits.
  52: - Do not remove humor; simply anchor the item (add display_name near first mention) and ensure custody-change sentences include the display_name.
  53: - Do not rename item_id or registry fields; only adjust prose wording.
  54: - Do not add numeric mechanics to invariants_add; store them in continuity system updates instead.
  55: - If an event appears in prose, it must appear in key_events.
  56: - must_stay_true must include milestone ledger entries and any inventory/injury/ownership invariants implied by prose.
  57: - Inventory posture reconciliation:
  58:   - If inventory/containers change (held/stowed/container), must_stay_true must be updated to the final posture.
  59:   - Add REMOVE lines for prior inventory/container invariants before the new final entries.
  60:   - Use canonical invariant formats:
  61:     - inventory: CHAR_X -> <item display_name> (status=held|carried|equipped|stowed, container=hand_left|hand_right|<container>)
  62:     - container: <container> (owner=CHAR_X, contents=[<item display_name>, ...])
  63: - character_updates entries must use arrays: persona_updates (array), invariants_add (array).
  64: - character_updates.inventory must be an array of objects, never item-id strings.
  65: - Inventory object shape: {"item": "ITEM_or_name", "container": "hand_left|hand_right|<container>", "status": "held|carried|equipped|stowed"}.
  66:   - Container object shape: {"container": "<name>", "owner": "CHAR_id", "contents": ["ITEM_id", "..."]}.
  67: - Use character_continuity_system_updates / global_continuity_system_updates to reconcile mechanics.
  68: - global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
  69:   - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
  70:   - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
  71: - If a new mechanic family appears in prose/UI, add it under set with a stable key.
  72: - All *_updates arrays must contain objects; never emit bare strings as array entries.
  73: - JSON shape guardrails (strict, do not deviate):
  74:   - character_updates MUST be an array of objects.
  75:     - INVALID: "character_updates": {"character_id": "CHAR_X"}
  76:     - VALID: "character_updates": [{"character_id": "CHAR_X"}]
  77:   - character_continuity_system_updates MUST be an array of objects with character_id.
  78:     - INVALID: "character_continuity_system_updates": {"set": {...}}
  79:     - VALID: "character_continuity_system_updates": [{"character_id": "CHAR_X", "set": {...}}]
  80:   - summary_update fields must be arrays of strings.
  81:     - INVALID: "summary_update": {"last_scene": "text"}
  82:     - VALID: "summary_update": {"last_scene": ["text"], "key_events": ["..."], "must_stay_true": ["..."], "chapter_so_far_add": ["..."]}
  83: - appearance_updates MUST be an object under character_updates.
  84:     - INVALID: "appearance_updates": [{"set": {...}}] OR "appearance_updates": {"marks_add": [...]}
  85:     - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
  86: - character_updates.containers must be an array of objects with at least: container, owner, contents (array).
  87: - Durable-state mutation blocks are mandatory when applicable:
  88: - Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
  89:   - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
  90:     - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
  91:     - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
  92:   - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
  93:     - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
  94:     - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]
  95: 
  96:   - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
  97:   - custodian must be a non-null string id/scope (character id or "world"). Never use null.
  98:     - INVALID: "custodian": null
  99:     - VALID: "custodian": "CHAR_ARTIE" or "world"
 100:   - owner_scope must be "character" or "world" and must match the custodian scope.
 101:   - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
 102:   - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.
 103: - Transfer vs registry conflict rule (must follow):
 104:   - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
 105:   - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
 106:   - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).  - `inventory_alignment_updates` for scene-fit posture normalization.
 107:   - `item_registry_updates` for durable item metadata/custody changes.
 108:   - `plot_device_updates` for durable plot-device custody/activation changes.
 109:   - `transfer_updates` for item handoffs (source, destination, reason, optional transfer_chain).
 110:   - Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
 111:   - `inventory_alignment_updates` must be an array of objects; never an object with an `updates` field.
 112:   - inventory_alignment_updates[*].set MUST be an object (not a list).
 113:     - INVALID: "set": []
 114:     - VALID:   "set": {"inventory": [...], "containers": [...]}
 115: - For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
 116: - If durable mutation is implied but ambiguous, keep canonical state unchanged and emit an explicit repair note in reason fields.
 117: - Honor scene-card durable constraints (`required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`; optional `required_visible_on_page`).
 118: - Respect `timeline_scope` and `ontological_scope`; avoid physical custody changes in non-present/non-real scope unless explicit override is present.
 119: - Scope override rule (non-present / non-real scenes):
 120:   - If timeline_scope != "present" OR ontological_scope != "real", do NOT emit durable mutation blocks UNLESS they are required for this scene transition (based on scene_card + current state).
 121:   - Durable mutation blocks include: inventory_alignment_updates, transfer_updates, item_registry_updates, plot_device_updates, and any other durable-state mutation you emit.
 122:   - If they are required for the story (e.g., items must persist into the next real scene, required_in_custody/required_scene_accessible lists them, or transition_type implies continuity of physical possessions), you MUST set scope_override=true (or allow_non_present_mutation=true) on EACH affected update object and set reason_category="timeline_override".
 123: Inputs
 124: - prose: final scene text
 125: - state: pre-scene state
 126: - draft_patch: patch returned by write/repair (may be incomplete)
 127: - continuity_pack: pre-write continuity pack
 128: - character_states: current cast-only character state
 129: 
 130: Scene card:
 131: {{scene_card}}
 132: 
 133: Continuity pack:
 134: {{continuity_pack}}
 135: 
 136: Character registry (id -> name):
 137: {{character_registry}}
 138: 
 139: Thread registry:
 140: {{thread_registry}}
 141: 
 142: Character states (per cast_present_ids):
 143: {{character_states}}
 144: 
 145: State (pre-scene):
 146: {{state}}
 147: 
 148: Summary (facts-only):
 149: {{summary}}
 150: 
 151: Draft state patch:
 152: {{draft_patch}}
 153: 
 154: Prose:
 155: {{prose}}
 156: 
 157: Item registry (canonical):
 158: {{item_registry}}
 159: 
 160: Plot devices (canonical):
 161: {{plot_devices}}
 162: 
 163: JSON Contract Block (strict; arrays only):
 164: - All *_updates must be arrays of objects, even when there is only one update.
 165: - INVALID vs VALID examples:
 166:   - item_registry_updates:
 167:     - INVALID: "item_registry_updates": {"set": {"ITEM_X": {...}}}
 168:     - VALID:   "item_registry_updates": [{"item_id": "ITEM_X", "set": {...}}]
 169:   - plot_device_updates:
 170:     - INVALID: "plot_device_updates": {"set": {"DEVICE_X": {...}}}
 171:     - VALID:   "plot_device_updates": [{"device_id": "DEVICE_X", "set": {...}}]
 172:   - transfer_updates:
 173:     - INVALID: "transfer_updates": {"item_id": "ITEM_X"}
 174:     - VALID:   "transfer_updates": [{"item_id": "ITEM_X", "reason": "handoff"}]
 175:   - inventory_alignment_updates:
 176:     - INVALID: "inventory_alignment_updates": {"updates": [{...}]}
 177:     - VALID:   "inventory_alignment_updates": [{"character_id": "CHAR_X", "set": {...}, "reason": "..."}]
 178:   - global_continuity_system_updates:
 179:     - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
 180:     - VALID:   "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
 181: - custodian must be a non-null string id or "world"; never null.
 182: 
 183: 
 184: 
 185: 
 186: 
 187: 
 188: 
 189: 
```
