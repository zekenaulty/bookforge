# Snapshot: output_contract.md

- Source: `resources/prompt_templates/output_contract.md`
- SHA256: `4FDAA9A34FD8B7857B675C366974B3D88CDB816C4CBDF1D0CF5FC69C7D25D5D0`
- Line count: `21`
- Byte length: `1959`

```text
   1: Output must follow the requested format.
   2: JSON blocks must be valid and schema-compliant.
   3: All required keys and arrays must be present.
   4: When a prompt specifies required counts or ranges, treat them as hard constraints.
   5: Do not collapse arrays below the stated minimums.
   6: If multiple output blocks are required (e.g. PROSE and STATE_PATCH), include all blocks in order.
   7: If output must be JSON only, return a single JSON object with no commentary or code fences.
   8: When creating outlines, the total scenes per chapter (sum of sections[].scenes[]) must match chapters[].pacing.expected_scene_count.
   9: If a prompt requires a COMPLIANCE or PREFLIGHT block, include it before PROSE.
  10: Durable vs ephemeral mechanics:
  11: - DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
  12: - EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
  13: - DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
  14: - EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene.
  15: For durable items, prose must use display_name; item_id is reserved for JSON/patches. The display_name must be human readable and not an escaped id/name.
  16: For durable mutations, every `transfer_updates[]` object must include `item_id` and `reason` (non-empty string).
  17: `inventory_alignment_updates` must be an array of objects (no wrapper object with `updates`).
  18: Use canonical continuity keys: character_continuity_system_updates and global_continuity_system_updates.
  19: - global_continuity_system_updates MUST be an array of objects. Each entry can include set/delta/remove/reason.
  20:   - INVALID: "global_continuity_system_updates": {"set": {"reality_stability": 94}}
  21:   - VALID: "global_continuity_system_updates": [{"set": {"reality_stability": 94}}]
```
