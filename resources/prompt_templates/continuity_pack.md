# CONTINUITY PACK

Create a continuity pack JSON object with these fields:
- scene_end_anchor: 2-4 factual sentences about how the last scene ended (no prose).
- constraints: list of immediate continuity constraints.
- open_threads: list of active thread ids.
- cast_present: list of character ids present next.
- location: location id or name.
- next_action: the implied next action.

Return ONLY JSON.

State:
{{state}}

Recent facts:
{{recent_facts}}
