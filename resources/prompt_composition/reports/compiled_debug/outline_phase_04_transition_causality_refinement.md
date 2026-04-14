<!-- begin entry=E001 semantic=outline_pipeline.phase_04.transition_causality_refinement_prompt_contract source=resources/prompt_blocks/phase/outline_pipeline/phase_04_transition_causality_refinement_prompt_contract.md repeat=1/1 -->
# OUTLINE PIPELINE PHASE 04A: TRANSITION SEAM ANALYSIS (CHAPTER-SCOPED)

Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.

Return ONLY a single JSON object. No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Required output schema:
{
  "schema_version": "transition_refine_v1",
  "outline": {
    "schema_version": "1.1",
    "chapters": [
      {
        "chapter_id": 1
      }
    ]
  },
  "phase_report": {
    "candidate_seams": [],
    "edits_applied": [],
    "transition_hint_compliance": []
  }
}

Chapter-scoped hard rules:
- Output MUST contain exactly one chapter in outline.chapters.
- The output chapter_id MUST match chapter_target_id.
- Do not echo the full book.
- Preserve required transition/link contracts for all scenes in this chapter.
- Preserve section.end_condition and section closure echo behavior in this chapter.

Required deterministic link rules (phase 04+):
- For every non-first scene in this chapter: consumes_outcome_from is required.
- For every non-last scene in this chapter: hands_off_to is required.
- For every non-last scene in this chapter: transition_out_text is required and non-empty.
- For every non-last scene in this chapter: transition_out_anchors is required (3-6 non-empty strings).
- Link format must be chapter_id:scene_id and must remain chapter-local.

Required transition contract fields:
- location_start_label, location_end_label, location_start, location_end, handoff_mode, constraint_state, transition_in_text, transition_in_anchors.
- location_start_id/location_end_id may be provided, but orchestrator generates canonical LOC_* ids from labels and validates membership in registry.
- seam_score (int 0-100) and seam_resolution (inline_bridge|micro_scene|full_scene).
- Do NOT emit placeholder identity values (current_location, unknown, placeholder, tbd, here, there) in location or transition fields.

Hard requirements for candidate_seams:
- You must evaluate every adjacent scene edge in this chapter before deciding candidate_seams.
- candidate_seams must include every seam in this chapter that requires non-trivial handling.
- requested_resolution must be one of: inline_bridge, micro_scene, full_scene.
- from_scene_ref and to_scene_ref must use chapter_id:scene_id format.
- If no seam candidates are needed, emit candidate_seams as an empty array.

Non-trivial seam triggers (ANY trigger means candidate consideration is required):
- meaningful location change (not just a camera-angle change in the same place)
- time jump (even minutes) without an on-page bridge beat
- focal attention or objective snaps to a new target
- prior scene ends high tension and next scene begins already elsewhere/settled
- continuity dependency (gear, injury, knowledge, social state) must carry visibly
- opening of next scene would read as teleportation or missing content

Resolution preference ladder:
- Prefer micro_scene by default when there is any meaningful gap.
- Use inline_bridge ONLY when all are true:
  - bridge can be realized in 1-2 sentences
  - no new beat is needed
  - no missing causal step exists
  - no continuity state can be misread without a new scene
- Use full_scene when a new beat is required (decision, conflict pivot, reveal, failure, bargain, chase, arrival with consequence) or when the seam is emotionally/causally important.

Seam-score mapping guidance:
- 0-25: smooth transition, usually no candidate required
- 26-50: candidate likely; inline_bridge or micro_scene depending on triggers
- 51-75: micro_scene strongly preferred
- 76-100: full_scene strongly preferred

Insertion expectation:
- If you find ANY seam_score >= 60 in this chapter, propose at least one micro_scene or full_scene candidate unless the chapter is truly continuous.

Strict hard-cut policy:
- In strict transition mode, hard_cut is disallowed.
- Convert any hard_cut scenes to a non-hard-cut handoff mode.
- Do not emit handoff_mode=hard_cut in strict mode.

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

Chapter target id:
{{chapter_target_id}}

Chapter input outline:
{{chapter_input_outline}}

Previous chapter context (read-only):
{{chapter_prev_outline}}

Next chapter context (read-only):
{{chapter_next_outline}}

Transition hints:
{{transition_hints}}

Scene count policy:
{{scene_count_policy}}

Book:
{{book}}

Targets:
{{targets}}

Notes:
{{notes}}
<!-- end entry=E001 semantic=outline_pipeline.phase_04.transition_causality_refinement_prompt_contract -->
