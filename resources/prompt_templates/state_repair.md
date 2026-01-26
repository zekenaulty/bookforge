# STATE REPAIR

You are the state repair step. You must output a corrected STATE_PATCH JSON only.
No prose, no commentary, no code fences.

Goal:
- Ensure state_patch fully and accurately captures the scene's events and outcomes.
- Fill missing summary_update data and fix invalid formats from draft_patch.
- Preserve state invariants; do not contradict must_stay_true.

Rules:
- Output a single JSON object that matches the state_patch schema.
- Use schema_version "1.0".
- Use scene_card.cast_present_ids for world_updates.cast_present.
- Use scene_card.thread_ids for world_updates.open_threads.
- Do not invent new character or thread ids.
- summary_update arrays are required: last_scene (2-4 sentences), key_events (3-7 bullets), must_stay_true (3-7 bullets), chapter_so_far_add (bullets).
- If an event appears in prose, it must appear in key_events.
- must_stay_true must include milestone ledger entries and any inventory/injury/ownership invariants implied by prose.
- character_updates entries must use arrays: persona_updates (array), invariants_add (array).

Inputs
- prose: final scene text
- state: pre-scene state
- draft_patch: patch returned by write/repair (may be incomplete)
- continuity_pack: pre-write continuity pack
- character_states: current cast-only character state

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

State (pre-scene):
{{state}}

Summary (facts-only):
{{summary}}

Draft state patch:
{{draft_patch}}

Prose:
{{prose}}
