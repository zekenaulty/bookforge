# REPAIR

Fix the scene based on lint issues.
Summaries are reference-only; do not recap them in prose unless scene_card explicitly requires recap.
Timeline Lock: only depict events explicitly listed in the current Scene Card. Do not depict, imply, or resolve later-scene milestones (acquisition, binding, reveals, travel arrival, injury changes) unless the Scene Card explicitly contains that milestone.
State primacy: state invariants and summary facts are binding; do not contradict them.
Milestone uniqueness: if a milestone is marked DONE in must_stay_true, do not depict it again. If marked NOT_YET, do not depict it now.
Spatial/inventory consistency: injuries, inventory, and ownership must remain consistent unless explicitly changed in the Scene Card.
Inventory contract: track ownership and container location for key items; update must_stay_true when items move or change hands.
For held items, specify container=hand_left or container=hand_right.
Numbers must be owned: any UI/prose number shown must exist in state or be added in the patch.
Skills must be owned: any skill names, ranks, cooldowns, or charges shown must exist in state or be added in the patch.
Canonical descriptors (colors, item names, effect IDs) must be reused exactly; do not paraphrase.
summary_update arrays are mandatory; do not omit or leave empty unless explicitly stated.
STATE_PATCH must record all major events and outcomes from the prose; if an event happens, add it to key_events and update must_stay_true as needed.
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
- Include character_stat_updates for cast_present_ids when stats change (set/delta).
- Include character_skill_updates for cast_present_ids when skills change (set/delta).
- Include run_stat_updates/run_skill_updates only if global mechanics change.
- Include character_updates entries for cast_present_ids that change state (inventory, containers, persona shifts).
  - Each entry must include character_id, chapter, scene, inventory (full current list), containers (full current list), invariants_add (array), persona_updates (array).
  - If you have a single persona update, still wrap it in an array of strings.
- must_stay_true must include a milestone ledger and invariants using standard phrasing, e.g.:
  - Avoid numeric stats in must_stay_true; store them in stats/skills updates instead.
  - inventory: CHAR_example -> shard (carried, container=satchel)
  - inventory: CHAR_example -> longsword (carried, container=hand_right)
  - container: satchel (owner=CHAR_example, contents=[shard, maps])
  - milestone: shard_bind = DONE/NOT_YET
  - milestone: maps_acquired = DONE/NOT_YET
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

Character states (per cast_present_ids):
{{character_states}}

Scene:
{{prose}}

State:
{{state}}
