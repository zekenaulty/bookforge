# WRITE

Write the scene described by the scene card.
- Start in motion. No recap.
- Use the continuity pack and state for continuity.
- Use character_registry to keep names consistent in prose.
- Return prose plus a state_patch JSON block.

STATE_PATCH rules:
- Use schema_version "1.0".
- Use world_updates to update world state (cast_present, location, recent_facts, open_threads).
- Use scene_card.cast_present_ids for cast_present (ids, not names).
- Use scene_card.thread_ids for open_threads (thread ids).
- Do not invent new character or thread ids.
- Use cursor_advance only if you need to override the default cursor.

Scene card:
{{scene_card}}

Continuity pack:
{{continuity_pack}}

Character registry (id -> name):
{{character_registry}}

Thread registry:
{{thread_registry}}

Style anchor:
{{style_anchor}}

State:
{{state}}

Output:
PROSE:
<scene prose>

STATE_PATCH:
<json>
