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
- If a required event is not in the Scene Card, do not perform it.
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
- Use cursor_advance only if you need to override the default cursor.
- Include character_updates entries for cast_present_ids that change state (inventory, containers, persona shifts).
  - Each entry must include character_id, chapter, scene, inventory (full current list), containers (full current list), invariants_add (array), persona_updates (array).
  - If you have a single persona update, still wrap it in an array of strings.
- must_stay_true must include a milestone ledger and invariants using standard phrasing, e.g.:
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
