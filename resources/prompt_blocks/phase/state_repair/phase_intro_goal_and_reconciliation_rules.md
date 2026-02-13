# STATE REPAIR

You are the state repair step. You must output a corrected STATE_PATCH JSON only.
No prose, no commentary, no code fences.

Goal:
- Ensure state_patch fully and accurately captures the scene's events and outcomes.
- Fill missing summary_update data and fix invalid formats from draft_patch.
- Preserve pre-scene invariants unless this scene changes them; when it does, update must_stay_true to the final end-of-scene value.
- must_stay_true reconciliation (mandatory):
  - If this scene changes a durable fact (stats/HP/status/title/custody), you MUST update must_stay_true to reflect the final end-of-scene value.
  - Remove or replace any prior must_stay_true entries that conflict with new durable values.
  - Do NOT carry forward conflicting legacy invariants once the scene updates them.

