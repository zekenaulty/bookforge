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
- Item naming enforcement scope:
  - Do not require that every mention in narrative prose use display_name.
  - Enforce canonical display_name for: (a) anchoring at first introduction (same paragraph or within the next 2 sentences),
    (b) any custody-change sentence (drop/pick up/hand off/stow/equip/transfer), and (c) any case where a descriptor is ambiguous among multiple durable items in the scene.
  - Otherwise, treat non-canonical descriptive references as warnings at most.
- Naming severity policy:
  - warning: unambiguous descriptor used post-anchor.
  - error: missing anchor, descriptor used during custody-change without canonical name, or ambiguity risk.
- For authoritative surfaces, prefer exact canonical item/device labels from registries.
- For milestone repetition/future checks, compare against PRE-INVARIANTS only (pre-scene canon).
- For ownership/consistency checks, compare against POST-STATE (post-patch candidate).
- Check for POV drift vs book POV (no first-person in third-person scenes).
  - Ignore first-person pronouns inside quoted dialogue; only narration counts.
- Deterministically enforce scene-card durable constraints (required_in_custody, required_scene_accessible, forbidden_visible, device_presence; optional required_visible_on_page).
- Durable constraint evaluation must use POST-STATE candidate (after patch), not pre-state.
- Report missing durable context ids with explicit retry hints instead of guessing canon.
- Input consistency check (mandatory, before issuing continuity/durable errors):
  - If MUST_STAY_TRUE invariants contradict the provided post-patch candidate character state, treat this as an upstream snapshot error.
  - In that case emit a single error issue with code "pipeline_state_incoherent" including evidence of the invariant and the conflicting state field.
  - Do NOT emit additional continuity errors for the same fields when pipeline_state_incoherent is present.
- For each issue, include evidence when possible (line number + excerpt) as {"evidence": {"line": N, "excerpt": "..."}}.
- Evaluate consistency over the full scope of the scene, not a single snapshot.
  - Transitional state: a temporary mismatch later corrected or superseded within this scene.
  - Durable violation: a mismatch that persists through the end of the scene or ends unresolved.
  - You MUST read the entire scene and build a minimal timeline of explicit state claims/updates (UI lines, inventory changes, title/skill changes, location/time claims).
  - If you detect an apparent inconsistency, you MUST search forward for later updates that resolve or supersede it.
  - Only produce FAIL for durable violations. If resolved within the scene, do NOT FAIL; at most emit a warning.
  - When the same stat appears multiple times, the last occurrence in the scene is authoritative unless an explicit rollback is stated.
  - Any durability violation must cite both the conflicting line and the lack of later correction (or state "no later correction found").

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
    {"code": "continuity", "message": "Example issue", "severity": "error"}
  ]
}

Scene:
{{prose}}

Authoritative surfaces:
{{authoritative_surfaces}}

Character states (post-patch candidate, per cast_present_ids):
{{character_states}}

Item registry (canonical):
{{item_registry}}

Plot devices (canonical):
{{plot_devices}}

Pre-state (before patch):
{{pre_state}}

Pre-summary (facts-only):
{{pre_summary}}

Pre-invariants (must_stay_true + key facts):
{{pre_invariants}}

Post-state candidate (after patch):
{{post_state}}

Post-summary (facts-only):
{{post_summary}}

Post-invariants (must_stay_true + key facts):
{{post_invariants}}
