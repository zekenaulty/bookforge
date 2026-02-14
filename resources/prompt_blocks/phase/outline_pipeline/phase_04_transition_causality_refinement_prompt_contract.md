# OUTLINE PIPELINE PHASE 04: TRANSITION AND CAUSALITY REFINEMENT

You are refining the outline draft for transition quality and causality.
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
    "edits_applied": []
  }
}

Goal:
- Ensure each scene outcome is consumed by the next 1-2 scenes.
- Eliminate abrupt section/scene edge transitions.
- Keep changes minimal and targeted.

Rules:
- Do not change core book premise or chapter goals.
- Prefer editing summaries/outcomes/type/edge fields over restructuring chapters.
- Transition scenes are allowed only if they include a concrete state change.
- Do not add recap scenes.
- Keep ids stable.
- If transition_hints are provided, enforce them unless they conflict with hard schema rules.

Consumption definition (acceptable):
- precondition, new pressure, new constraint, new goal, new cost, new opportunity.

Required phase_report semantics:
- orphan_outcomes_after must be 0.
- weak_handoffs_after should be as low as possible.
- edits_applied should briefly list targeted edits.

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

