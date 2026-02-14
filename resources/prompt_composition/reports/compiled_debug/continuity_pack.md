<!-- begin entry=E001 semantic=continuity_pack.prompt_contract_and_constraints source=resources/prompt_blocks/phase/continuity_pack/prompt_contract_and_constraints.md repeat=1/1 -->
# CONTINUITY PACK

Create a continuity pack JSON object with these fields:
- scene_end_anchor: 2-4 factual sentences about how the last scene ended (no prose).
- constraints: list of immediate continuity constraints.
- open_threads: list of active thread ids.
- cast_present: list of character names present next.
- location: location id or name.
- next_action: the implied next action.
- summary: echo state.summary (facts-only arrays; do not paraphrase).

Return ONLY JSON.

Rules:
- Use only characters listed in scene_card.cast_present. Do not introduce new names.
- summary must match state.summary and remain facts-only; do not add prose.
- constraints must include the highest-priority invariants from summary.must_stay_true and summary.key_facts_ring (copy exact strings when possible).
- constraints must include the highest-priority inventory/container invariants from summary.must_stay_true (copy exact strings when possible).
- If character_states are provided, prefer their inventory/container facts and continuity mechanic facts; do not invent conflicting values.
- If item_registry or plot_devices are provided, reuse canonical names/ids in constraints when referencing durable items/devices.
- Prefer item_registry.items[].display_name for prose references; reserve item_id for canonical JSON. The display_name must be human readable and not an escaped id/name.
- If state.global_continuity_system_state contains canonical mechanic labels/values, reuse those exact labels in constraints.
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

Character states (per cast_present_ids):
{{character_states}}

State:
{{state}}

Summary (facts-only):
{{summary}}

Recent facts:
{{recent_facts}}
Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}

<!-- end entry=E001 semantic=continuity_pack.prompt_contract_and_constraints -->
