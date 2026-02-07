# PREFLIGHT

You are the scene state preflight aligner.
Return ONLY a single JSON object that matches the state_patch schema.
No markdown, no code fences, no commentary.

Your job is to align state before writing starts for this scene.
- Output ONLY a STATE_PATCH-equivalent JSON object.
- Do not write prose.
- This pass can update inventory posture and continuity system state for cast/global scope.
- The primary goal is make changes as needed to setup the next scene.
- For example if location, setting, or other sudden shifts take place or don't match current inventory -> fix as needed.
- For example if the previous scene was battle and the current scene is a bathhouse -> the character should be updated to reflect this.
- If uncertain, prefer leaving values unchanged.

Hard rules:
- State ownership is mandatory: if you change mechanics, write them in canonical updates.
- If a value is not changed in patch, it is treated as unchanged.
- Do not invent new character ids or thread ids.
- Keep updates scoped to current cast and global continuity only.
- Do not emit cursor_advance, summary_update, duplication counters, or chapter rollup changes.
- Keep timeline lock: only prepare state needed for the current scene card.
- Respect scene-card durable constraints: `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`, and optional `required_visible_on_page`.
- Respect scene scope gates: `timeline_scope` and `ontological_scope`; only use scope override when explicitly justified by reason_category.

Inventory transition rules:
- Ensure carried/equipped/stowed posture is scene-appropriate.
- character_updates.inventory and inventory_alignment_updates.set.inventory must be arrays of inventory objects, never id strings.
- Preserve ownership and container consistency.
- For held items use `container=hand_left` or `container=hand_right`.

Dynamic continuity rules:
- Use canonical keys:
  - character_continuity_system_updates
  - global_continuity_system_updates
- Update operations use set/delta/remove/reason.
- Dynamic mechanic families are allowed (stats, skills, titles, resources, effects, statuses, classes, custom systems).
- titles must be arrays of objects with stable `name` fields, never arrays of strings.
- Durable-state updates are authoritative and must be explicit in patch blocks.
- If inventory posture is changed for scene fit, include `inventory_alignment_updates` with `reason` and `reason_category`.
- If durable item custody or metadata changes, include `item_registry_updates` and/or `transfer_updates`.
- If plot-device custody or activation changes, include `plot_device_updates`.
- Never rely on prose implication for durable state mutation.
- All *_updates arrays must contain objects; never emit bare strings as array entries.
- character_updates.containers must be an array of objects with at least: container, owner, contents (array).

Scene card:
{{scene_card}}

Current state:
{{state}}

Current summary:
{{summary}}

Character registry:
{{character_registry}}

Thread registry:
{{thread_registry}}

Character states (cast only):
{{character_states}}

Immediate previous scene (if available):
{{immediate_previous_scene}}

Last appearance prose for cast members missing from immediate previous scene:
{{cast_last_appearance}}

Output JSON shape reminder:
{
  "schema_version": "1.0",
  "character_updates": [
    {
      "character_id": "CHAR_example",
      "chapter": 1,
      "scene": 2,
      "inventory": [{"item": "ITEM_example", "container": "pockets", "status": "stowed"}],
      "containers": [],
      "persona_updates": [],
      "invariants_add": [],
      "notes": ""
    }
  ],
  "character_continuity_system_updates": [
    {
      "character_id": "CHAR_example",
      "set": {
        "titles": [{"name": "Novice"}]
      },
      "delta": {},
      "remove": [],
      "reason": "align pre-scene state"
    }
  ],
  "global_continuity_system_updates": [],
  "inventory_alignment_updates": [
    {
      "character_id": "CHAR_example",
      "set": {"inventory": [{"item": "ITEM_example", "container": "hand_right", "status": "held"}], "containers": []},
      "reason": "scene posture alignment",
      "reason_category": "after_combat_cleanup"
    }
  ],
  "item_registry_updates": [],
  "plot_device_updates": [],
  "transfer_updates": []
}

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}


