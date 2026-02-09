# LINT

Check the scene for continuity, invariant violations, and duplication.
Flag invariant contradictions against must_stay_true/key facts.
Return ONLY JSON matching the lint_report schema.
- Classify UI/prose mechanic claims as DURABLE or EPHEMERAL before enforcing.
  - DURABLE: persistent stats/caps, skills/titles acquired, lasting status effects, inventory/custody, named mechanics referenced as invariants.
  - EPHEMERAL: roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat telemetry.
- Enforce DURABLE claims against authoritative_surfaces/state/registries.
- EPHEMERAL claims do not require state ownership; only flag EPHEMERAL contradictions inside the same scene as warnings.
- If uncertain, default to EPHEMERAL (warning at most), not DURABLE (error).
- status="fail" only if there is at least one issue with severity="error"; warnings alone => status="pass".
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
