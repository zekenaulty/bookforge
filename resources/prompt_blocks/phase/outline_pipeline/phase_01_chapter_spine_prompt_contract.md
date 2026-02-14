# OUTLINE PIPELINE PHASE 01: CHAPTER SPINE

You are generating the chapter spine only.
Return ONLY a single JSON object. No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Goal:
- Produce a stable chapter-level backbone before section/scene planning.
- Do NOT emit sections, scenes, threads, or character stubs in this phase.

Required output schema:
{
  "schema_version": "spine_v1",
  "chapters": [
    {
      "chapter_id": 1,
      "title": "",
      "goal": "",
      "chapter_role": "hook",
      "stakes_shift": "",
      "bridge": {"from_prev": "", "to_next": ""},
      "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 10}
    }
  ]
}

Rules:
- chapter_id must be unique integers.
- chapter_role should use preferred vocabulary when possible:
  hook, setup, pressure, reversal, revelation, investigation, journey, trial, alliance, betrayal, siege, confrontation, climax, aftermath, transition, hinge.
- tempo should use preferred vocabulary when possible: slow_burn, steady, rush.
- pacing.intensity should be 1-5.
- stakes_shift must represent movement, not static restatement.
- bridge.to_next must be a plausible consequence of chapter goal + stakes_shift.
- expected_scene_count is a soft target, not a hard fixed count.

Validation intent:
- The next phase will build section architecture from this chapter spine.
- Keep wording concise and unambiguous.

Book:
{{book}}

Targets:
{{targets}}

User prompt (optional):
{{user_prompt}}

Notes:
{{notes}}

Transition hints (optional):
{{transition_hints}}

