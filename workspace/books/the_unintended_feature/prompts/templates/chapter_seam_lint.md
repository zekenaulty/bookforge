# CHAPTER SEAM LINT

Evaluate only the seam between Scene A and Scene B.
Return ONLY JSON matching the lint_report schema.

Goal:
- Detect seam problems at the local boundary between the end of Scene A and the beginning of Scene B.
- Focus on duplication, altered UI carryover, repeated physical state, restart energy, tense/mode drift, repeated regrounding, and scaffold leakage.
- Treat the scenes as already-written prose that must now read as one continuous flow.

Hard rules:
- Judge only the boundary, not the whole chapter.
- Preserve factual continuity. Do not invent missing plot.
- If the boundary is already clean, return status="pass" with issues=[].
- status="fail" only if there is at least one issue with severity="error".
- warnings alone still mean status="pass".

Issue guidance:
- Use code `duplicate_ui_surface` when the same UI/system block is repeated across the seam.
- Use code `ui_value_drift` when the same UI/mechanic surface appears with altered values or labels across the seam without an in-story reason.
- Use code `restart_energy_overlap` when Scene B replays the same beat or bodily state instead of advancing.
- Use code `overlap_lead_sentence` when Scene B's opening sentence materially overlaps Scene A's close.
- Use code `repeated_anchor_regrounding` when the same anchor phrase or physical grounding is restated across the seam.
- Use code `tense_shift_at_join` when narration mode or tense changes abruptly at the boundary.
- Use code `scaffold_leakage` when the boundary reads like planning language, recap scaffolding, or non-prose instruction residue.

Required keys:
- schema_version ("1.0")
- status ("pass" or "fail")
- issues (array of objects)

Each issue object must include:
- code
- message
Optional:
- severity
- evidence

If there are no issues, return:
{
  "schema_version": "1.0",
  "status": "pass",
  "issues": []
}

If there are issues, return:
{
  "schema_version": "1.0",
  "status": "fail",
  "issues": [
    {"code": "restart_energy_overlap", "message": "Example issue", "severity": "error"}
  ]
}

Scene pair:
{{pair_payload}}

Deterministic seam findings:
{{deterministic_issues}}
