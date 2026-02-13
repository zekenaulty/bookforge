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

