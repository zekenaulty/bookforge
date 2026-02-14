Output must follow the requested format.
JSON blocks must be valid and schema-compliant.
All required keys and arrays must be present.
When a prompt specifies required counts or ranges, treat them as hard constraints.
Do not collapse arrays below the stated minimums.
If multiple output blocks are required (e.g. PROSE and STATE_PATCH), include all blocks in order.
If output must be JSON only, return a single JSON object with no commentary or code fences.
When creating outlines, follow the active scene-count policy:
- Exact mode: total scenes per chapter (sum of sections[].scenes[]) must match chapters[].pacing.expected_scene_count.
- Range mode: chapter totals must remain within the configured range and still align with pacing intent.
If a prompt requires a COMPLIANCE or PREFLIGHT block, include it before PROSE.
Durable vs ephemeral mechanics:
- DURABLE mechanics = persistent stats/caps, skills/titles, lasting status effects, inventory/custody, permanent buffs/debuffs.
- EPHEMERAL UI/telemetry = roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat logs.
- DURABLE mechanics must be owned by continuity system state (or added via STATE_PATCH in the same output).
- EPHEMERAL readouts do NOT require state ownership unless the scene explicitly intends them to persist beyond this scene.
For durable items, prose must use display_name; item_id is reserved for JSON/patches. The display_name must be human readable and not an escaped id/name.
For durable mutations, every `transfer_updates[]` object must include `item_id` and `reason` (non-empty string).
`inventory_alignment_updates` must be an array of objects (no wrapper object with `updates`).
Use canonical continuity keys: character_continuity_system_updates and global_continuity_system_updates.
