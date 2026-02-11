# STATE REPAIR

You are the state repair step. You must output a corrected STATE_PATCH JSON only.
No prose, no commentary, no code fences.

Goal:
- Ensure state_patch fully and accurately captures the scene's events and outcomes.
- Fill missing summary_update data and fix invalid formats from draft_patch.
- Preserve state invariants; do not contradict must_stay_true.
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
  - plot_device_updates: set must include name, custody_scope, custody_ref, activation_state, linked_threads, constraints, last_seen {chapter, scene, location}. Optional: display_name, aliases, linked_item_id.
  - If you introduce a new item_id/device_id anywhere in this patch, you MUST include a corresponding registry update with the full required fields.
  - `inventory_alignment_updates` for scene-fit posture normalization.
  - `item_registry_updates` for durable item metadata/custody changes.
  - `plot_device_updates` for durable plot-device custody/activation changes.
  - `transfer_updates` for item handoffs (source, destination, reason, optional transfer_chain).
  - Every `transfer_updates` entry must include `item_id` and `reason` (non-empty string).
  - `inventory_alignment_updates` must be an array of objects; never an object with an `updates` field.
- For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
- If durable mutation is implied but ambiguous, keep canonical state unchanged and emit an explicit repair note in reason fields.
- Honor scene-card durable constraints (`required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`; optional `required_visible_on_page`).
- Respect `timeline_scope` and `ontological_scope`; avoid physical custody changes in non-present/non-real scope unless explicit override is present.

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



