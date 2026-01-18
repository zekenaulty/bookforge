# CONTINUITY PACK

Create a continuity pack JSON object with these fields:
- scene_end_anchor: 2-4 factual sentences about how the last scene ended (no prose).
- constraints: list of immediate continuity constraints.
- open_threads: list of active thread ids.
- cast_present: list of character names present next.
- location: location id or name.
- next_action: the implied next action.

Return ONLY JSON.

Rules:
- Use only characters listed in scene_card.cast_present. Do not introduce new names.
- If scene_card.cast_present is empty, cast_present must be an empty array.
- open_threads must be a subset of thread_registry thread_id values.
- If scene_card.thread_ids is present, prefer those thread ids.
- Do not invent new thread ids or character names.

Scene card:
{{scene_card}}

Character registry (id -> name):
{{character_registry}}

Thread registry:
{{thread_registry}}

State:
{{state}}

Recent facts:
{{recent_facts}}
