# WRITE

Write the scene described by the scene card.
- YOU MUST ALWAYS RETURN PROSE AND THE STATE_PATCH.
- Start in motion. No recap.
- Summaries are reference-only; do not recap them in prose unless scene_card explicitly requires recap.
- Use the continuity pack and state for continuity.
- Use character_registry to keep names consistent in prose.
- Timeline Lock: only depict events explicitly listed in the current Scene Card. Do not depict, imply, or resolve later-scene milestones (acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
- State primacy: state invariants and summary facts are binding; do not contradict them.
- Milestone uniqueness: if a milestone is marked DONE in must_stay_true, do not depict it again. If marked NOT_YET, do not depict it now.
- Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
- Inventory contract: track ownership and container location for key items; update must_stay_true when items move or change hands.
- For held items, specify container=hand_left or container=hand_right.
- Continuity system ownership is mandatory, and must be tracked: any mechanic/UI numbers, skills, titles, classes, ranks, resources, cooldowns, effects, statuses, or future mechanic families must be sourced from existing continuity system state or written into continuity system updates in this scene.
- titles are arrays of objects with stable name fields; do not emit titles as plain strings.
- Canonical descriptors (colors, item names, effect IDs, mechanic labels) must be reused exactly; do not paraphrase.
- If item_registry or plot_devices are provided, they are canonical durable-state references for ownership/custody labels in authoritative outputs.
- If a required event is not in the Scene Card, do not perform it.
- Enforce scene-card durable constraints: honor `required_in_custody`, `required_scene_accessible`, `forbidden_visible`, and `device_presence`; treat `required_visible_on_page` as explicit narrative requirement when present.
- Respect `timeline_scope` and `ontological_scope` when proposing durable mutations; do not mutate physical custody in non-present/non-real scope unless explicitly marked override.
- summary_update arrays are mandatory; do not omit or leave empty unless explicitly stated.
- STATE_PATCH must record all major events and outcomes from the prose; if an event happens, add it to key_events and update must_stay_true as needed.
- must_stay_true must include a milestone ledger entry for every milestone referenced in the Scene Card or already present in state.
- If state lacks a key invariant needed for this scene, seed it in must_stay_true using standard phrasing.
- Return prose plus a state_patch JSON block.

STATE_PATCH rules:
- Use schema_version "1.0".
- Use world_updates to update world state (cast_present, location, recent_facts, open_threads).
- Use scene_card.cast_present_ids for cast_present (ids, not names).
- Use scene_card.thread_ids for open_threads (thread ids).
- Do not invent new character or thread ids.
- Include summary_update arrays: last_scene (array of 2-4 sentence strings), key_events (array of 3-7 bullet strings), must_stay_true (array of 3-7 bullet strings), chapter_so_far_add (array of bullet strings).
- Include story_so_far_add only at chapter end (or when scene_card explicitly requests).
- Use threads_touched only if you can reference thread ids from scene_card.thread_ids.
- Include character_continuity_system_updates for cast_present_ids when mechanics change.
  - Use set/delta/remove/reason.
  - Use nested families under set/delta (examples): stats, skills, titles, resources, effects, statuses, classes, ranks.
  - titles must be arrays of objects with stable name fields (example: [{"name": "Novice", "source": "starting_class", "active": true}]).
  - If a new mechanic family appears, add it under set with a stable key.
- Include global_continuity_system_updates only if global mechanics change.
- Durable-state mutation blocks are mandatory when applicable:
  - `inventory_alignment_updates` for scene-fit posture normalization.
  - `item_registry_updates` for durable item metadata/custody changes.
  - `plot_device_updates` for durable plot-device custody/activation changes.
  - `transfer_updates` for item handoffs (source, destination, reason, optional transfer_chain).
- For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
- If you mutate durable state, do not leave the same mutation only in prose.
- Include character_updates entries for cast_present_ids that change state (inventory, containers, persona shifts).
  - Each entry must include character_id, chapter, scene, inventory (full current list), containers (full current list), invariants_add (array), persona_updates (array).
  - If you have a single persona update, still wrap it in an array of strings.
- must_stay_true must include a milestone ledger and invariants using standard phrasing, e.g.:
  - Avoid numeric mechanics in must_stay_true; store them in continuity system updates instead.
  - inventory: CHAR_example -> shard (carried, container=satchel)
  - inventory: CHAR_example -> longsword (carried, container=hand_right)
  - container: satchel (owner=CHAR_example, contents=[shard, maps])
  - milestone: shard_bind = DONE/NOT_YET
  - milestone: maps_acquired = DONE/NOT_YET
  - injury: right forearm scar / left arm filament
  - ownership: shard (carried) / shard (bound but physical)

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

Style anchor:
{{style_anchor}}

State:
{{state}}

Output (required, no code fences):
COMPLIANCE:
Scene ID: <scene_card.scene_id>
Allowed events: <short list from Scene Card>
Forbidden milestones: <from must_stay_true>
Current arm-side / inventory facts: <from must_stay_true>

PROSE:
<scene prose>

STATE_PATCH:
<json>

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}

