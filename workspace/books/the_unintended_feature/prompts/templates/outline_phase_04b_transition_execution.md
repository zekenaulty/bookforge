# OUTLINE PIPELINE PHASE 04B: TRANSITION EXECUTION (CHAPTER-SCOPED)

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
    "inserted_scene_refs": [],
    "resolved_candidates": [],
    "insertion_edge_impacts": [],
    "blocked_by_budget": [],
    "unresolved_required_insertions": [],
    "edits_applied": []
  }
}

Goal:
- Execute selected transition seam resolutions for this chapter only.
- For selected micro_scene/full_scene candidates, you MUST author inserted transition scenes.
- Do not leave selected insertion candidates unresolved.

Chapter-scoped hard rules:
- Output MUST contain exactly one chapter in outline.chapters.
- The output chapter_id MUST match chapter_target_id.
- Do not echo the full book.

Inputs for deterministic routing context (chapter-scoped):
- Selected candidates to execute:
{{phase_04_selected_candidates_json}}

- Selected insertion candidates (micro/full only):
{{phase_04_selected_insertions_json}}

- Blocked candidates (for reporting only):
{{phase_04_blocked_candidates_json}}

- Policy context and exact-mode conflict markers:
{{phase_04_policy_context_json}}

- Full 04A output (read-only):
{{outline_phase_04a_output}}

Hard execution rules:
- Every selected candidate with requested_resolution micro_scene/full_scene must be resolved in this output.
- For requested_resolution micro_scene/full_scene, resolved means an inserted scene object exists between from_scene_ref and to_scene_ref.
- If a selected insertion cannot be satisfied, return error_v1 (do not emit partial success).
- Downgrading selected insertion candidates to inline_bridge is forbidden.
- Inserted scenes must be authored prose semantics; do not emit meta/fallback phrasing.
- Do not synthesize placeholder identity values (current_location, unknown, placeholder, tbd, here, there).
- Preserve required transition/link contracts and chapter-local scene sequencing.
- After insertions, re-evaluate section boundaries: the LAST scene in each section must include end_condition_echo equal to the section's end_condition. If insertions changed which scene is last, move/copy end_condition_echo accordingly (do not drop it).

Resolved candidate reporting:
- phase_report.resolved_candidates must contain one entry for each selected insertion candidate in this chapter.
- Use chapter_id:scene_id refs.
- Each resolved insertion entry must include:
  - from_scene_ref
  - to_scene_ref
  - requested_resolution
  - resolution (must equal requested_resolution for selected insertion candidates)
  - inserted_scene_ref (chapter_id:scene_id of the inserted scene)
- Every inserted_scene_ref listed in resolved_candidates must also appear in phase_report.inserted_scene_refs.
- IMPORTANT: from_scene_ref and to_scene_ref in resolved_candidates must match the original selected insertion candidates exactly (copy them verbatim from phase_04_selected_insertions_json). Do not renumber those refs in the report, even if scene numbering changes after insertion.
- Do not include resolved_candidates entries for inline_bridge selections.
- Do not include resolved_candidates entries for edges not in phase_04_selected_insertions_json.

Insertion impact reporting (required when any insertion occurs):
- phase_report.insertion_edge_impacts must include one entry per inserted scene in this chapter.
- Each entry must include:
  - from_scene_ref (the scene that now hands off to the inserted scene)
  - to_scene_ref (the scene that now consumes the inserted scene)
  - inserted_scene_ref (chapter_id:scene_id of the inserted scene)
  - requested_resolution
  - resolution (must match requested_resolution)

If you cannot satisfy constraints after correction attempts, return error_v1:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "error_type": "validation_error",
  "reason_code": "phase04b_required_insertion_unresolved",
  "missing_fields": ["phase_report.resolved_candidates"],
  "phase": "phase_04b_transition_execution",
  "action_hint": "Resolve every selected insertion candidate with authored scene content and report each resolution."
}

Chapter target id:
{{chapter_target_id}}

Chapter input outline:
{{chapter_input_outline}}

Previous chapter context (read-only):
{{chapter_prev_outline}}

Next chapter context (read-only):
{{chapter_next_outline}}

Book:
{{book}}

Targets:
{{targets}}

Notes:
{{notes}}
