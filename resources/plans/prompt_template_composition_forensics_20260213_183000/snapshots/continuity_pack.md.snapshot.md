# Snapshot: continuity_pack.md

- Source: `resources/prompt_templates/continuity_pack.md`
- SHA256: `F3E97B8B5B5C0139A232DEA15B26A8403975ECAE8D9AE60053D1433EB83CB192`
- Line count: `52`
- Byte length: `2176`

```text
   1: # CONTINUITY PACK
   2: 
   3: Create a continuity pack JSON object with these fields:
   4: - scene_end_anchor: 2-4 factual sentences about how the last scene ended (no prose).
   5: - constraints: list of immediate continuity constraints.
   6: - open_threads: list of active thread ids.
   7: - cast_present: list of character names present next.
   8: - location: location id or name.
   9: - next_action: the implied next action.
  10: - summary: echo state.summary (facts-only arrays; do not paraphrase).
  11: 
  12: Return ONLY JSON.
  13: 
  14: Rules:
  15: - Use only characters listed in scene_card.cast_present. Do not introduce new names.
  16: - summary must match state.summary and remain facts-only; do not add prose.
  17: - constraints must include the highest-priority invariants from summary.must_stay_true and summary.key_facts_ring (copy exact strings when possible).
  18: - constraints must include the highest-priority inventory/container invariants from summary.must_stay_true (copy exact strings when possible).
  19: - If character_states are provided, prefer their inventory/container facts and continuity mechanic facts; do not invent conflicting values.
  20: - If item_registry or plot_devices are provided, reuse canonical names/ids in constraints when referencing durable items/devices.
  21: - Prefer item_registry.items[].display_name for prose references; reserve item_id for canonical JSON. The display_name must be human readable and not an escaped id/name.
  22: - If state.global_continuity_system_state contains canonical mechanic labels/values, reuse those exact labels in constraints.
  23: - If scene_card.cast_present is empty, cast_present must be an empty array.
  24: - open_threads must be a subset of thread_registry thread_id values.
  25: - If scene_card.thread_ids is present, prefer those thread ids.
  26: - Do not invent new thread ids or character names.
  27: 
  28: Scene card:
  29: {{scene_card}}
  30: 
  31: Character registry (id -> name):
  32: {{character_registry}}
  33: 
  34: Thread registry:
  35: {{thread_registry}}
  36: 
  37: Character states (per cast_present_ids):
  38: {{character_states}}
  39: 
  40: State:
  41: {{state}}
  42: 
  43: Summary (facts-only):
  44: {{summary}}
  45: 
  46: Recent facts:
  47: {{recent_facts}}
  48: Item registry (canonical):
  49: {{item_registry}}
  50: 
  51: Plot devices (canonical):
  52: {{plot_devices}}
```
