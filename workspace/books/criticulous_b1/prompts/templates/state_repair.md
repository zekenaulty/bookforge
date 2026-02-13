# STATE REPAIR

You are the state repair step. You must output a corrected STATE_PATCH JSON only.
No prose, no commentary, no code fences.

Goal:
- Ensure state_patch fully and accurately captures the scene's events and outcomes.
- Fill missing summary_update data and fix invalid formats from draft_patch.
- Preserve pre-scene invariants unless this scene changes them; when it does, update must_stay_true to the final end-of-scene value.
- must_stay_true reconciliation (mandatory):
  - If this scene changes a durable fact (stats/HP/status/title/custody), you MUST update must_stay_true to reflect the final end-of-scene value.
  - Remove or replace any prior must_stay_true entries that conflict with new durable values.
  - Do NOT carry forward conflicting legacy invariants once the scene updates them.

- must_stay_true removal (mandatory when a durable fact is superseded):
  - Add "REMOVE: <exact prior invariant text>" in summary_update.must_stay_true.
  - Place REMOVE lines before the new final invariant.
  - REMOVE lines also apply to key_facts_ring (purge stale facts from continuity).

- Ensure mechanic/UI ownership in continuity system updates.

Rules:
- Output a single JSON object that matches the state_patch schema.
- Use schema_version "1.0".
- Use scene_card.cast_present_ids for world_updates.cast_present.
- Use scene_card.thread_ids for world_updates.open_threads.
- Do not invent new character or thread ids.
- summary_update arrays are required: last_scene (2-4 sentences), key_events (3-7 bullets), must_stay_true (3-7 bullets), chapter_so_far_add (bullets).
- Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates
Durable vs ephemeral mechanics:
- UI gate: only include bracketed UI blocks when scene_card.ui_allowed=true. If false, remove or rephrase UI blocks into narrative prose.

- If a DURABLE mechanic appears multiple times in the scene (e.g., base values then final values), the LAST occurrence is canonical.
- You MUST capture the canonical end-of-scene values in character_continuity_system_updates.
- When allocation/level-up happens, update all affected point pools (e.g., stat_points, skill_points, perk_points) if shown.
- Do not treat early UI snapshots as canonical if the scene later corrects them.
- DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
- EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
- DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
- EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene..
- titles are arrays of objects with stable name fields; do not emit titles as plain strings.
- Canonical descriptors (colors, item names, effect IDs, mechanic labels) must be reused exactly; do not paraphrase.
- If item_registry or plot_devices are provided, they are canonical durable-state references for authoritative labels and custody terms.
- Use item_registry.items[].display_name in prose; use item_id only in patches/JSON. The display_name must be human readable and not an escaped id/name.
Appearance contract:
- Attire boundary: wearables are inventory-owned. Do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
- appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change.
- Durable appearance changes must be declared in scene_card.durable_appearance_changes (or an explicit appearance milestone) and recorded via appearance_updates.
- If prose depicts a durable appearance change, include character_updates.appearance_updates with a reason.
- Do NOT set summary or art text in appearance_updates (derived after acceptance).

Naming repairs:
- If lint flags an item naming issue, fix it with minimal edits.
- Do not remove humor; simply anchor the item (add display_name near first mention) and ensure custody-change sentences include the display_name.
- Do not rename item_id or registry fields; only adjust prose wording.
- Do not add numeric mechanics to invariants_add; store them in continuity system updates instead.
- If an event appears in prose, it must appear in key_events.
- must_stay_true must include milestone ledger entries and any inventory/injury/ownership invariants implied by prose.
- Inventory posture reconciliation:
  - If inventory/containers change (held/stowed/container), must_stay_true must be updated to the final posture.
  - Add REMOVE lines for prior inventory/container invariants before the new final entries.
  - Use canonical invariant formats:
    - inventory: CHAR_X -> <item display_name> (status=held|carried|equipped|stowed, container=hand_left|hand_right|<container>)
    - container: <container> (owner=CHAR_X, contents=[<item display_name>, ...])
- character_updates entries must use arrays: persona_updates (array), invariants_add (array).
- character_updates.inventory must be an array of objects, never item-id strings.
- Inventory object shape: {"item": "ITEM_or_name", "container": "hand_left|hand_right|<container>", "status": "held|carried|equipped|stowed"}.
  - Container object shape: {"container": "<name>", "owner": "CHAR_id", "contents": ["ITEM_id", "..."]}.
- Use character_continuity_system_updates / global_continuity_system_updates to reconcile mechanics.

- global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
  - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
  - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]

- If a new mechanic family appears in prose/UI, add it under set with a stable key.
- All *_updates arrays must contain objects; never emit bare strings as array entries.
- JSON shape guardrails (strict, do not deviate):
  - character_updates MUST be an array of objects.
    - INVALID: "character_updates": {"character_id": "CHAR_X"}
    - VALID: "character_updates": [{"character_id": "CHAR_X"}]
  - character_continuity_system_updates MUST be an array of objects with character_id.
    - INVALID: "character_continuity_system_updates": {"set": {...}}
    - VALID: "character_continuity_system_updates": [{"character_id": "CHAR_X", "set": {...}}]
  - summary_update fields must be arrays of strings.
    - INVALID: "summary_update": {"last_scene": "text"}
    - VALID: "summary_update": {"last_scene": ["text"], "key_events": ["..."], "must_stay_true": ["..."], "chapter_so_far_add": ["..."]}
- appearance_updates MUST be an object under character_updates.
    - INVALID: "appearance_updates": [{"set": {...}}] OR "appearance_updates": {"marks_add": [...]}
    - VALID: "appearance_updates": {"set": {"marks_add": [{"name": "Singed Hair", "location": "head", "durability": "durable"}]}, "reason": "..."}
- character_updates.containers must be an array of objects with at least: container, owner, contents (array).
- Durable-state mutation blocks are mandatory when applicable:
- Required fields for durable registry entries (when creating NEW ids or filling missing required fields):
  - item_registry_updates MUST be an array of objects. Each entry requires item_id and can include set/delta/remove/reason.
    - INVALID: item_registry_updates = {"set": {"ITEM_X": {...}}}
    - VALID: item_registry_updates = [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates MUST be an array of objects. Each entry requires device_id and can include set/delta/remove/reason.
    - INVALID: plot_device_updates = {"set": {"DEVICE_X": {...}}}
    - VALID: plot_device_updates = [{"device_id": "DEVICE_X", "set": {...}}]

  - item_registry_updates: set must include name, type, owner_scope, custodian, linked_threads, state_tags, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_device_id, replacement_of.
  - custodian must be a non-null string id/scope (character id or "world"). Never use null.
    - INVALID: "custodian": null
    - VALID: "custodian": "CHAR_ARTIE" or "world"
  - owner_scope must be "character" or "world" and must match the custodian scope.
  - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
  - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.

- Transfer vs registry conflict rule (must follow):
  - If you create a NEW item in item_registry_updates with final custodian already set (e.g., CHAR_ARTIE), DO NOT emit transfer_updates for that item.
  - If you emit transfer_updates for a NEW item, the registry entry must start with custodian="world" and then transfer to the character.
  - expected_before must match the registry entry at the moment of transfer (after any registry update that applies before it).  - `inventory_alignment_updates` for scene-fit posture normalization.
  - `item_registry_updates` for durable item metadata/custody changes.
  - `plot_device_updates` for durable plot-device custody/activation changes.
  - `transfer_updates` for item handoffs (source, destination, reason, optional transfer_chain).
  - Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
  - `inventory_alignment_updates` must be an array of objects; never an object with an `updates` field.

  - inventory_alignment_updates[*].set MUST be an object (not a list).
    - INVALID: "set": []
    - VALID:   "set": {"inventory": [...], "containers": [...]}
- For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
- If durable mutation is implied but ambiguous, keep canonical state unchanged and emit an explicit repair note in reason fields.
- Honor scene-card durable constraints (`required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`; optional `required_visible_on_page`).
- Respect `timeline_scope` and `ontological_scope`; avoid physical custody changes in non-present/non-real scope unless explicit override is present.

- Scope override rule (non-present / non-real scenes):
  - If timeline_scope != "present" OR ontological_scope != "real", do NOT emit durable mutation blocks UNLESS they are required for this scene transition (based on scene_card + current state).
  - Durable mutation blocks include: inventory_alignment_updates, transfer_updates, item_registry_updates, plot_device_updates, and any other durable-state mutation you emit.
  - If they are required for the story (e.g., items must persist into the next real scene, required_in_custody/required_scene_accessible lists them, or transition_type implies continuity of physical possessions), you MUST set scope_override=true (or allow_non_present_mutation=true) on EACH affected update object and set reason_category="timeline_override".

Inputs
- prose: final scene text
- state: pre-scene state
- draft_patch: patch returned by write/repair (may be incomplete)
- continuity_pack: pre-write continuity pack
- character_states: current cast-only character state

Scene card:
{{scene_card}}

Continuity pack:
{{continuity_pack}}

Character registry (id -> name):
{{character_registry}}

Thread registry:
{{thread_registry}}

Character states (per cast_present_ids):
{{character_states}}

State (pre-scene):
{{state}}

Summary (facts-only):
{{summary}}

Draft state patch:
{{draft_patch}}

Prose:
{{prose}}

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}


JSON Contract Block (strict; arrays only):
- All *_updates must be arrays of objects, even when there is only one update.
- INVALID vs VALID examples:
  - item_registry_updates:
    - INVALID: "item_registry_updates": {"set": {"ITEM_X": {...}}}
    - VALID:   "item_registry_updates": [{"item_id": "ITEM_X", "set": {...}}]
  - plot_device_updates:
    - INVALID: "plot_device_updates": {"set": {"DEVICE_X": {...}}}
    - VALID:   "plot_device_updates": [{"device_id": "DEVICE_X", "set": {...}}]
  - transfer_updates:
    - INVALID: "transfer_updates": {"item_id": "ITEM_X"}
    - VALID:   "transfer_updates": [{"item_id": "ITEM_X", "reason": "handoff"}]
  - inventory_alignment_updates:
    - INVALID: "inventory_alignment_updates": {"updates": [{...}]}
    - VALID:   "inventory_alignment_updates": [{"character_id": "CHAR_X", "set": {...}, "reason": "..."}]
  - global_continuity_system_updates:
    - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
    - VALID:   "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
- custodian must be a non-null string id or "world"; never null.

