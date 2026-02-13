  - inventory_alignment_updates[*].set MUST be an object (not a list).
    - INVALID: "set": []
    - VALID:   "set": {"inventory": [...], "containers": [...]}
- For off-screen normalization and non-trivial durable mutations, include `reason_category` with stable values like `time_skip_normalize`, `location_jump_normalize`, `after_combat_cleanup`, `stowed_at_inn`, `handoff_transfer`, `knowledge_reveal`.
- If durable mutation is implied but ambiguous, keep canonical state unchanged and emit an explicit repair note in reason fields.
- Honor scene-card durable constraints (`required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`; optional `required_visible_on_page`).
- Respect `timeline_scope` and `ontological_scope`; avoid physical custody changes in non-present/non-real scope unless explicit override is present.

