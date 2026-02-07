# LINT

Check the scene for continuity, invariant violations, and duplication.
Flag invariant contradictions against must_stay_true/key facts.
Return ONLY JSON matching the lint_report schema.
- Check and require that any UI mechanic values in prose are owned by continuity system state and match candidate values.
- Treat only authoritative surfaces as canonical-check targets; do not enforce canonical labels in narrative prose.
- For authoritative surfaces, prefer exact canonical item/device labels from registries.
- Check for POV drift vs book POV (no first-person in third-person scenes).
- Deterministically enforce scene-card durable constraints (`required_in_custody`, `required_scene_accessible`, `forbidden_visible`, `device_presence`; optional `required_visible_on_page`).
- Report missing durable context ids with explicit retry hints instead of guessing canon.

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

Authoritative surfaces:
{{authoritative_surfaces}}

Character states (per cast_present_ids):
{{character_states}}

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}

State:
{{state}}

Summary (facts-only):
{{summary}}

Invariants (must_stay_true + key facts):
{{invariants}}