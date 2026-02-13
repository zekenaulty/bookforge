<!-- begin entry=E001 semantic=lint.lint_policy_rules_and_inputs source=resources/prompt_blocks/phase/lint/lint_policy_rules_and_inputs.md repeat=1/1 -->
# LINT

Check the scene for continuity, invariant violations, and duplication.
Flag invariant contradictions against must_stay_true/key facts.
Return ONLY JSON matching the lint_report schema.
- Classify UI/prose mechanic claims as DURABLE or EPHEMERAL before enforcing.
  - DURABLE: persistent stats/caps, skills/titles acquired, lasting status effects, inventory/custody, named mechanics referenced as invariants.
  - EPHEMERAL: roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat telemetry.
- Enforce DURABLE claims against authoritative_surfaces/state/registries.
- EPHEMERAL claims do not require state ownership; only flag EPHEMERAL contradictions inside the same scene as warnings.
- UI gate:
  - If scene_card.ui_allowed=false and any authoritative UI blocks appear, emit issue code 'ui_gate_violation' (severity depends on lint mode).
  - If ui_allowed is missing and UI blocks appear, emit 'ui_gate_unknown' (warning) requesting explicit ui_allowed; do not fail solely for missing flag.
  - Inline bracketed UI (e.g., [HP: 1/1]) is still UI and should be gated the same way; do not embed UI mid-sentence.
- If uncertain, default to EPHEMERAL (warning at most), not DURABLE (error).
- status="fail" only if there is at least one issue with severity="error"; warnings alone => status="pass".
- Item naming enforcement scope:
  - Do not require that every mention in narrative prose use display_name.
  - Enforce canonical display_name for: (a) anchoring at first introduction (same paragraph or within the next 2 sentences),
    (b) any custody-change sentence (drop/pick up/hand off/stow/equip/transfer), and (c) any case where a descriptor is ambiguous among multiple durable items in the scene.
  - Otherwise, treat non-canonical descriptive references as warnings at most.
- Prose hygiene: flag internal ids or container codes in narrative prose (CHAR_, ITEM_, THREAD_, DEVICE_, hand_left, hand_right).
- Naming severity policy:
  - warning: unambiguous descriptor used post-anchor.
  - error: missing anchor, descriptor used during custody-change without canonical name, or ambiguity risk.

- Appearance enforcement (authoritative surface):
  - APPEARANCE_CHECK is authoritative for cast_present_ids.
  - Compare APPEARANCE_CHECK tokens to appearance_current atoms/marks (alias-aware).
  - If APPEARANCE_CHECK contradicts appearance_current, emit error code "appearance_mismatch".
  - Prose-only appearance contradictions are warnings unless explicitly durable and uncorrected in-scene.
  - If prose depicts a durable appearance change but scene_card.durable_appearance_changes does not include it and no appearance_updates are present, emit error code "appearance_change_undeclared".
  - If APPEARANCE_CHECK is missing for a cast member, emit warning code "appearance_check_missing".
- For authoritative surfaces, prefer exact canonical item/device labels from registries.
- For milestone repetition/future checks, compare against PRE-INVARIANTS only (pre-scene canon).
- For ownership/consistency checks, compare against POST-STATE (post-patch candidate).
- POST-STATE is canonical; character_states is a derived convenience view. If they contradict, emit pipeline_state_incoherent.
- Check for POV drift vs book POV (no first-person in third-person scenes).
  - Ignore first-person pronouns inside quoted dialogue; only narration counts.
- Deterministically enforce scene-card durable constraints (required_in_custody, required_scene_accessible, forbidden_visible, device_presence; optional required_visible_on_page).
- Durable constraint evaluation must use POST-STATE candidate (after patch), not pre-state.
- Report missing durable context ids with explicit retry hints instead of guessing canon.
- Input consistency check (mandatory, before issuing continuity/durable errors):
  - If MUST_STAY_TRUE invariants contradict the provided post-patch candidate character state, treat this as an upstream snapshot error.
  - In that case emit a single error issue with code "pipeline_state_incoherent" including evidence of the invariant and the conflicting state field.
  - Do NOT emit additional continuity errors for the same fields when pipeline_state_incoherent is present.
- must_stay_true removals:
  - Lines starting with "REMOVE:" are deletion directives, not invariants.
  - Ignore REMOVE lines when checking contradictions.
  - If a REMOVE directive targets a fact, treat that fact as non-canonical even if it appears earlier in must_stay_true.
- If pipeline_state_incoherent is present, issues MUST contain exactly one issue.
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

Scene card:
{{scene_card}}

Authoritative surfaces:
{{authoritative_surfaces}}

Appearance check (authoritative):
{{appearance_check}}

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



<!-- end entry=E001 semantic=lint.lint_policy_rules_and_inputs -->
