<!-- begin entry=E001 semantic=outline_pipeline.phase_03.scene_draft_prompt_contract source=resources/prompt_blocks/phase/outline_pipeline/phase_03_scene_draft_prompt_contract.md repeat=1/1 -->
# OUTLINE PIPELINE PHASE 03: SCENE DRAFT

Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.

Return ONLY a single JSON object that matches outline schema v1.1.
No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Core contract:
- Each scene is one writing unit.
- Every scene must include type and outcome.
- outcome must be a concrete state change.
- Do not pad with travel/recap/mood-only scenes.

Required top-level keys:
- schema_version ("1.1")
- chapters (array)

Registry policy:
- characters and threads are globally recommended.
- If any scene references character ids, top-level characters becomes required.
- If any scene references thread ids, top-level threads becomes required.

Required chapter/section/scene constraints:
- chapter_id must be sequential integers starting at 1.
- section_id must be sequential integers within each chapter.
- scene_id is chapter-local and must be monotonic across all sections in that chapter.
- Each section-final scene must include end_condition_echo that exactly matches phase-02 end_condition.

Required transition fields (phase 03 and later):
- location_start (non-empty string)
- location_end (non-empty string)
- handoff_mode (enum string)
- constraint_state (enum string)
- transition_in_text (non-empty string; connective action, not recap)
- transition_in_anchors (array of 3-6 non-empty strings)
- For non-first scenes: consumes_outcome_from (required, chapter_id:scene_id)
- For non-last scenes: transition_out (required, non-empty) and hands_off_to (required, chapter_id:scene_id)

Transition enum guidance:
- handoff_mode: direct_continuation, escorted_transfer, detained_then_release, time_skip, hard_cut, montage, offscreen_processing, combat_disengage, arrival_checkpoint, aftermath_relocation
- constraint_state: free, pursued, detained, processed, sheltered, restricted, engaged_combat, fleeing

Seam scoring fields are optional in phase 03 but recommended:
- seam_score (0-100 int)
- seam_resolution (inline_bridge|micro_scene|full_scene)

Compatibility and omission rule:
- If a field is optional, omit when unknown; do NOT emit empty strings.
- Legacy transition_in may be present only as a compatibility alias; canonical field is transition_in_text.

Output must remain compatible with scene-count policy:
{{scene_count_policy}}

If you cannot satisfy constraints after correction attempts, return error_v1:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "phase": "phase_03_scene_draft",
  "reasons": ["..."],
  "validator_evidence": [{"code": "validation_code", "message": "...", "path": "json.path", "scene_ref": "chapter:scene"}],
  "retryable": false
}

Outline spine (phase 01):
{{outline_spine_v1}}

Section architecture (phase 02):
{{outline_sections_v1}}

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
<!-- end entry=E001 semantic=outline_pipeline.phase_03.scene_draft_prompt_contract -->
