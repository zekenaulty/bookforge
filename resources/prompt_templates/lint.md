# LINT

Check the scene for continuity, invariant violations, and duplication.
Flag invariant contradictions against must_stay_true/key facts.
Return ONLY JSON matching the lint_report schema.
- Check that any UI numbers or skill values in prose match state stats/skills. If not, emit a failure.
- Check for POV drift vs book POV (no first-person in third-person scenes).

Required keys:
- schema_version ("1.0")
- status ("pass" or "fail")
- issues (array of objects)

Each issue object must include:
- code
- message
Optional:
- severity

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
    {"code": "continuity", "message": "Example issue", "severity": "error"}
  ]
}

Scene:
{{prose}}


Character states (per cast_present_ids):
{{character_states}}

State:
{{state}}

Summary (facts-only):
{{summary}}

Invariants (must_stay_true + key facts):
{{invariants}}
