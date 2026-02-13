- Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
- Inventory contract: track ownership and container location for key items; update must_stay_true when items move or change hands.
- Inventory posture reconciliation:
  - If inventory/containers change (held/stowed/container), must_stay_true must be updated to the final posture.
  - Add REMOVE lines for prior inventory/container invariants before the new final entries.
  - Use canonical invariant formats:
    - inventory: CHAR_X -> <item display_name> (status=held|carried|equipped|stowed, container=hand_left|hand_right|<container>)
    - container: <container> (owner=CHAR_X, contents=[<item display_name>, ...])

- For held items, specify container=hand_left or container=hand_right.
- Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates.
Durable vs ephemeral mechanics:
- If a DURABLE mechanic appears multiple times in the scene (e.g., base values then final values), the LAST occurrence is canonical.
- You MUST capture the canonical end-of-scene values in character_continuity_system_updates.
- When allocation/level-up happens, update all affected point pools (e.g., stat_points, skill_points, perk_points) if shown.
- Do not treat early UI snapshots as canonical if the scene later corrects them.
- DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
- EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
- UI gate: only include bracketed UI blocks when scene_card.ui_allowed=true. If false, do not include UI blocks; rephrase into narrative prose.
- UI/system readouts must be on their own line, starting with '[' and ending with ']'.
- Do NOT embed bracketed UI in narrative sentences.
- Allowed suffix after a UI block is punctuation or a short parenthetical annotation (e.g., (locked), (Warning: ...)).

- DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
- EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene.
- titles are arrays of objects with stable name fields; do not emit titles as plain strings.
- If item_registry or plot_devices are provided, they are canonical durable-state references for ownership/custody labels in authoritative outputs.
- Use item_registry.items[].display_name in prose; use item_id only in patches/JSON. The display_name must be human readable and not an escaped id/name.
Appearance contract:
- Attire boundary: wearables are inventory-owned. Do not set appearance_current.attire unless scene_card declares signature_outfit; otherwise treat attire as derived from equipped inventory.
- appearance_current atoms/marks are canonical and must not be contradicted unless the Scene Card explicitly marks a durable appearance change.
- Durable appearance changes must be declared in scene_card.durable_appearance_changes (or an explicit appearance milestone) and recorded via appearance_updates.
- If a durable appearance change occurs in this scene, record it in character_updates.appearance_updates with a reason.
- APPEARANCE_CHECK is required in COMPLIANCE for each cast_present_id (4-8 tokens from atoms/marks).

Durable item naming discipline:
- When you first describe a durable item, anchor it by using the canonical display_name within the same paragraph (or within the next 2 sentences).
- After anchoring, you may use brief descriptors for style if unambiguous.
- During any custody/handling change, include the canonical display_name in that sentence.
- If a required event is not in the Scene Card, do not perform it.
- Enforce scene-card durable constraints: honor `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, and `device_presence`; treat `required_visible_on_page` as explicit narrative requirement when present.
- Respect `timeline_scope` and `ontological_scope` when proposing durable mutations; do not mutate physical custody in non-present/non-real scope unless explicitly marked override.

