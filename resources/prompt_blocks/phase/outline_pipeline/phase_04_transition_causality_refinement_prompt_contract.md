# OUTLINE PIPELINE PHASE 04A: TRANSITION SEAM ANALYSIS

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
    "candidate_seams": [
      {
        "from_scene_ref": "1:1",
        "to_scene_ref": "1:2",
        "seam_score": 72,
        "requested_resolution": "micro_scene",
        "reason": "location + custody jump requires realized handoff"
      }
    ],
    "transition_hint_compliance": [
      {"hint_id": "HINT_1", "satisfied": true, "evidence_scene_refs": ["1:1"]}
    ]
  }
}

Goal:
- Analyze scene seams and identify where inline bridging is sufficient versus where insertion is required.
- Keep changes minimal and targeted.

Required deterministic link rules (phase 04+):
- For every non-first scene in a chapter: consumes_outcome_from is required.
- For every non-last scene in a chapter: hands_off_to is required.
- For every non-last scene in a chapter: transition_out_text is required and non-empty.
- For every non-last scene in a chapter: transition_out_anchors is required (3-6 non-empty strings).
- Link format must be chapter_id:scene_id.
- Cross-chapter links are out-of-scope in these fields.
- Preserve section.end_condition for every section.
- Preserve section closure anchors (end_condition_echo on section-final scenes).

Required transition contract fields:
- location_start_label, location_end_label, location_start, location_end, handoff_mode, constraint_state, transition_in_text, transition_in_anchors.
- location_start_id/location_end_id may be provided, but orchestrator generates canonical LOC_* ids from labels and validates membership in registry.
- seam_score (int 0-100) and seam_resolution (inline_bridge|micro_scene|full_scene).
- Do NOT emit placeholder identity values (current_location, unknown, placeholder, tbd, here, there) in location or transition fields.

Hard requirements for candidate_seams:
- candidate_seams must include every seam that requires non-trivial handling.
- requested_resolution must be one of: inline_bridge, micro_scene, full_scene.
- from_scene_ref and to_scene_ref must use chapter_id:scene_id format.
- If no seam candidates are needed, emit candidate_seams as an empty array.

Strict hard-cut policy:
- In strict transition mode, hard_cut is disallowed.
- Convert any hard_cut scenes to a non-hard-cut handoff mode.
- Do not preserve or emit handoff_mode=hard_cut in strict mode.

If you cannot satisfy constraints after correction attempts, return error_v1:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "error_type": "validation_error",
  "reason_code": "phase04a_candidate_contract_invalid",
  "missing_fields": ["phase_report.candidate_seams"],
  "phase": "phase_04a_transition_seam_analysis",
  "action_hint": "Populate candidate seams with valid refs, scores, and resolution classes."
}

Outline draft (phase 03):
{{outline_draft_v1_1}}

Transition hints (author/system):
{{transition_hints}}

Scene count policy:
{{scene_count_policy}}

Book:
{{book}}

Targets:
{{targets}}

Notes:
{{notes}}
