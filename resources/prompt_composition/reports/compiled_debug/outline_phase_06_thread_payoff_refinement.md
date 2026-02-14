<!-- begin entry=E001 semantic=outline_pipeline.phase_06.thread_payoff_refinement_prompt_contract source=resources/prompt_blocks/phase/outline_pipeline/phase_06_thread_payoff_refinement_prompt_contract.md repeat=1/1 -->
# OUTLINE PIPELINE PHASE 06: THREAD AND PAYOFF REFINEMENT

Timeline Lock does not apply during outlining; you are planning, not writing a Scene Card.

Return ONLY a single JSON object matching outline schema v1.1.
No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Goal:
- Produce final release-ready outline with thread cadence and bridge coherence.
- Preserve transition and cast integrity from prior phases.

Required top-level keys:
- schema_version ("1.1")
- chapters (array)

Registry policy:
- characters and threads are recommended globally.
- If scene references require them, top-level arrays become required.

Required integrity:
- Keep chapter_id sequential and scene_id monotonic chapter-local.
- Preserve required transition link fields and format from phase 04/05.
- Preserve section closure anchors (end_condition_echo on section-final scenes).
- Maintain reference-integrity for all character/thread ids.

Thread policy:
- Target multiple touches per thread (default target >=3 is warning-oriented unless strict mode is configured).
- Prefer escalation over repeated identical beat.

Bridge policy:
- chapter.bridge.to_next should be reflected in next chapter opening intent/scene.
- Prefer minimal edits that keep existing structure.

Use scene-count policy:
{{scene_count_policy}}

If you cannot satisfy constraints after correction attempts, return error_v1:
{
  "result": "ERROR",
  "schema_version": "error_v1",
  "phase": "phase_06_thread_payoff_refinement",
  "reasons": ["..."],
  "validator_evidence": [{"code": "validation_code", "message": "...", "path": "json.path", "scene_ref": "chapter:scene"}],
  "retryable": false
}

Cast-refined outline (phase 05):
{{outline_cast_refined_v1_1}}

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
<!-- end entry=E001 semantic=outline_pipeline.phase_06.thread_payoff_refinement_prompt_contract -->
