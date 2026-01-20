# REPAIR

Fix the scene based on lint issues.
Summaries are reference-only; do not recap them in prose unless scene_card explicitly requires recap.
Return corrected prose plus a corrected state_patch JSON block.

Output format (required, no code fences, no commentary):
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
- Include summary_update with last_scene (2-4 factual sentences), key_events (3-7 bullets), must_stay_true (3-7 bullets), chapter_so_far_add (bullets).
- Include story_so_far_add only at chapter end (or when scene_card explicitly requests).
- Use threads_touched only if you can reference thread ids from scene_card.thread_ids.

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
