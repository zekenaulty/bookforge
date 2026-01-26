# REPAIR

Fix the scene based on lint issues.
Summaries are reference-only; do not recap them in prose unless scene_card explicitly requires recap.
Timeline Lock: only depict events explicitly listed in the current Scene Card. Do not depict, imply, or resolve later-scene milestones (acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
State primacy: state invariants and summary facts are binding; do not contradict them.
Milestone uniqueness: if a milestone is marked DONE in must_stay_true, do not depict it again. If marked NOT_YET, do not depict it now.
Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
summary_update arrays are mandatory; do not omit or leave empty unless explicitly stated.
must_stay_true must include a milestone ledger entry for every milestone referenced in the Scene Card or already present in state.
If state lacks a key invariant needed for this scene, seed it in must_stay_true using standard phrasing.
Return corrected prose plus a corrected state_patch JSON block.

Output format (required, no code fences, no commentary):
COMPLIANCE:
Scene ID: <scene_card.scene_id>
Allowed events: <short list from Scene Card>
Forbidden milestones: <from must_stay_true>
Current arm-side / inventory facts: <from must_stay_true>

PROSE:
<scene prose>

STATE_PATCH:
<json>

STATE_PATCH rules:
- Use schema_version "1.0".
- Use world_updates to update world state (cast_present, location, recent_facts, open_threads).
- Use scene_card.cast_present_ids for cast_present (ids, not names).
- Use scene_card.thread_ids for open_threads (thread ids).
- Do not invent new character or thread ids.
- Include summary_update arrays: last_scene (array of 2-4 sentence strings), key_events (array of 3-7 bullet strings), must_stay_true (array of 3-7 bullet strings), chapter_so_far_add (array of bullet strings).
- Include story_so_far_add only at chapter end (or when scene_card explicitly requests).
- Use threads_touched only if you can reference thread ids from scene_card.thread_ids.
- must_stay_true must include a milestone ledger and invariants using standard phrasing, e.g.:
  - milestone: shard_bind = DONE/NOT_YET
  - milestone: maps_acquired = DONE/NOT_YET
  - inventory: longsword (carried) / short-blade (carried)
  - injury: right forearm scar / left arm filament
  - ownership: shard (carried) / shard (bound but physical)

Issues:
{{issues}}

Scene card:
{{scene_card}}

Character registry (id -> name):
{{character_registry}}

Thread registry:
{{thread_registry}}

Scene:
{{prose}}

State:
{{state}}
