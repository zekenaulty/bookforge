# OUTLINE PIPELINE PHASE 04: TRANSITION AND CAUSALITY REFINEMENT

Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.

Return ONLY a single JSON object. No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Required output schema:
{
  "schema_version": "transition_refine_v1",
  "outline": {
    "schema_version": "1.1",
    "chapters": []
  },
  "phase_report": {
    "orphan_outcomes_before": 0,
    "orphan_outcomes_after": 0,
    "weak_handoffs_after": 0,
    "orphan_scene_refs_after": [],
    "weak_handoff_refs_after": [],
    "edits_applied": [],
    "transition_hint_compliance": [
      {"hint_id": "HINT_1", "satisfied": true, "evidence_scene_refs": ["1:1"]}
    ]
  }
}

Goal:
- Ensure each scene outcome is consumed by a nearby next scene.
- Eliminate abrupt section/scene edge transitions.
- Keep changes minimal and targeted.

Required deterministic link rules (phase 04+):
- For every non-first scene in a chapter: consumes_outcome_from is required.
- For every non-last scene in a chapter: hands_off_to is required.
- Link format must be chapter_id:scene_id.
- Cross-chapter links are out-of-scope in these fields.
- Preserve section closure anchors (end_condition_echo on section-final scenes).

Transition hint strict-mode requirement:
- If strict_transition_hints mode is active, phase_report.transition_hint_compliance must include every hint with satisfied=true or explicit unsatisfied explanation.
- evidence_scene_refs must use chapter_id:scene_id format.

If you cannot satisfy constraints after correction attempts, return error_v1:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "phase": "phase_04_transition_causality_refinement",
  "reasons": ["..."],
  "validator_evidence": [{"code": "validation_code", "message": "...", "path": "json.path", "scene_ref": "chapter:scene"}],
  "retryable": false
}

Outline draft (phase 03):
{{outline_draft_v1_1}}

Transition hints (author/system):
{{transition_hints}}

Book:
{{book}}

Targets:
{{targets}}

Notes:
{{notes}}
