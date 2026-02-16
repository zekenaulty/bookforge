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
- For every non-last scene in a chapter: transition_out_text is required and non-empty.
- For every non-last scene in a chapter: transition_out_anchors is required (3-6 non-empty strings).
- Link format must be chapter_id:scene_id.
- Cross-chapter links are out-of-scope in these fields.
- Preserve section.end_condition for every section.
- Preserve section closure anchors (end_condition_echo on section-final scenes).
- Preserve outline schema-required keys and types for chapter/section/scene objects.
  - Do not remove or rename required keys: goal, chapter_role, stakes_shift, bridge, pacing, intent, summary, characters.
- Preserve canonical registry key names:
  - characters[] uses character_id/name/intro
  - threads[] uses thread_id/label/status
- Forbidden aliases:
  - characters[].id, characters[].title, characters[].description
  - threads[].id, threads[].title, threads[].description

Required transition contract fields:
- location_start_label, location_end_label, location_start, location_end, handoff_mode, constraint_state, transition_in_text, transition_in_anchors
- location_start_id/location_end_id may be provided, but orchestrator generates canonical LOC_* ids from labels and validates membership in registry.
- seam_score (int 0-100) and seam_resolution (inline_bridge|micro_scene|full_scene)
- Do NOT emit placeholder identity values (current_location, unknown, placeholder, tbd, here, there) in location or transition fields.
- Strict hard-cut policy:
  - In strict transition mode, hard_cut is disallowed.
  - Convert any hard_cut scenes to a non-hard-cut handoff mode (for example time_skip, offscreen_processing, arrival_checkpoint, or combat_disengage).
  - Do not preserve or emit handoff_mode=hard_cut in strict mode.
- Hard-cut normalization checklist (required):
  - Scan ALL scenes for handoff_mode=hard_cut.
  - For EACH hard_cut scene, change handoff_mode to a non-hard-cut mode in strict mode.
  - hard_cut_justification and intentional_cinematic_cut may be retained for historical trace only, but handoff_mode must no longer be hard_cut.

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
  "error_type": "validation_error",
  "reason_code": "transition_contract_incomplete",
  "missing_fields": ["outline.chapters[0].sections[0].scenes[1].transition_out_text"],
  "phase": "phase_04_transition_causality_refinement",
  "action_hint": "Populate required transition links/anchors and concrete location labels."
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
