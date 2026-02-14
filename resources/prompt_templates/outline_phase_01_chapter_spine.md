# OUTLINE PIPELINE PHASE 01: CHAPTER SPINE

Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.

Return ONLY a single JSON object. No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Goal:
- Produce chapter-level structure only.
- Do NOT emit sections, scenes, threads, or character stubs.

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
- chapter_id must be sequential integers starting at 1.
- chapter_role should use preferred vocabulary when possible:
  hook, setup, pressure, reversal, revelation, investigation, journey, trial, alliance, betrayal, siege, confrontation, climax, aftermath, transition, hinge.
- tempo should use preferred vocabulary when possible: slow_burn, steady, rush.
- pacing.intensity should be 1-5.
- stakes_shift must represent movement, not static restatement.
- bridge.to_next must be a plausible consequence of chapter goal + stakes_shift.
- Keep chapter count stable across retries unless input constraints force change.
- Use this policy input when selecting expected_scene_count:
{{scene_count_policy}}

If you cannot satisfy constraints after correction attempts, return error_v1:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "phase": "phase_01_chapter_spine",
  "reasons": ["..."],
  "validator_evidence": [{"code": "validation_code", "message": "...", "path": "json.path"}],
  "retryable": false
}

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
