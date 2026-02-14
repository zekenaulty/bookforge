- For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
- If you mutate durable state, do not leave the same mutation only in prose.
- Include character_updates entries for cast_present_ids that change state (inventory, containers, persona shifts).
- appearance_updates: when a durable appearance change happens, include appearance_updates on the relevant character_updates entry.

