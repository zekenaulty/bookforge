Return corrected prose plus a corrected state_patch JSON block.

Output format (required, no code fences, no commentary):
COMPLIANCE:
Scene ID: <scene_card.scene_id>
Allowed events: <short list from Scene Card>
Forbidden milestones: <from must_stay_true>
Current arm-side / inventory facts: <from must_stay_true>

APPEARANCE_CHECK:
- CHAR_ID: <4-8 tokens from atoms/marks>

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
- Include character_continuity_system_updates for cast_present_ids when mechanics change.
  - Use set/delta/remove/reason.
  - Use nested families under set/delta (examples): stats, skills, titles, resources, effects, statuses, classes, ranks.
  - titles must be arrays of objects with stable name fields (example: [{"name": "Novice", "source": "starting_class", "active": true}]).
  - If a new mechanic family appears, add it under set with a stable key.
- Include global_continuity_system_updates only if global mechanics change.

