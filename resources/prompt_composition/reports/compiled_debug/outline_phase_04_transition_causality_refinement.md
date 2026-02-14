<!-- begin entry=E001 semantic=outline_pipeline.phase_04.transition_causality_refinement_prompt_contract source=resources/prompt_blocks/phase/outline_pipeline/phase_04_transition_causality_refinement_prompt_contract.md repeat=1/1 -->
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
- For every non-last scene in a chapter: transition_out is required and non-empty.
- Link format must be chapter_id:scene_id.
- Cross-chapter links are out-of-scope in these fields.
- Preserve section closure anchors (end_condition_echo on section-final scenes).

Required transition contract fields:
- location_start, location_end, handoff_mode, constraint_state, transition_in_text, transition_in_anchors
- seam_score (int 0-100) and seam_resolution (inline_bridge|micro_scene|full_scene)
- If handoff_mode=hard_cut and strict transition mode is active, include:
  - hard_cut_justification (non-empty)
  - intentional_cinematic_cut=true

Budget and downgrade reporting:
- If seam candidates are blocked by insertion budget, include phase_report.blocked_by_budget entries with scene_ref and seam_score when available.
- If a seam is downgraded (for example micro_scene -> inline_bridge), include phase_report.downgraded_resolution entries with scene_ref and reason.

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
<!-- end entry=E001 semantic=outline_pipeline.phase_04.transition_causality_refinement_prompt_contract -->
