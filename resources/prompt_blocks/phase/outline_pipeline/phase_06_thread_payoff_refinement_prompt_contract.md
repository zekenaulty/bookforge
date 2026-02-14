# OUTLINE PIPELINE PHASE 06: THREAD AND PAYOFF REFINEMENT

You are producing the final release outline.
Return ONLY a single JSON object matching outline schema v1.1.
No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Goal:
- Ensure thread cadence, escalation, and payoff readiness across chapters.
- Ensure chapter bridge.to_next is supported by chapter endings and next-chapter openings.
- Preserve transition and cast improvements from prior phases.

Required top-level keys:
- schema_version ("1.1")
- chapters (array)

Recommended top-level keys:
- threads (array)
- characters (array)

Thread rules:
- Every declared thread should be touched multiple times (default target >= 3).
- Thread touches should escalate (setup -> complication -> escalation/payoff pressure).
- Avoid repeated identical beats.

Bridge rules:
- chapter.bridge.to_next must be reflected in the next chapter's opening intent/scene.
- If bridge alignment is weak, minimally edit scene summaries/outcomes/edge fields.

Transition rules:
- Maintain concrete scene outcomes.
- Keep outcome-consumption continuity intact.
- Keep transition_in/transition_out/edge_intent fields coherent when present.

Cast rules:
- Preserve introduction correctness and recurring-role utility established in phase 05.

Output ordering guidance:
- chapters first, then threads, then characters.

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

