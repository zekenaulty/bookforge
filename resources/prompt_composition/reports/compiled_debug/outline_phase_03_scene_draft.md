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

Optional edge fields:
- transition_in, transition_out, edge_intent, consumes_outcome_from, hands_off_to
- If unknown, omit the field. Do NOT emit empty strings.
- If present, consumes_outcome_from/hands_off_to must use "chapter_id:scene_id" format (example "2:7").

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
