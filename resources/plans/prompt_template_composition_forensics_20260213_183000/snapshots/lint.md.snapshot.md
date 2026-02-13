# Snapshot: lint.md

- Source: `resources/prompt_templates/lint.md`
- SHA256: `F3B131D17E0E7779FA5A4CA7344DD5A557EF8AFB1D68B6FC75613E503F3A9F0A`
- Line count: `129`
- Byte length: `6887`

```text
   1: # LINT
   2: 
   3: Check the scene for continuity, invariant violations, and duplication.
   4: Flag invariant contradictions against must_stay_true/key facts.
   5: Return ONLY JSON matching the lint_report schema.
   6: - Classify UI/prose mechanic claims as DURABLE or EPHEMERAL before enforcing.
   7:   - DURABLE: persistent stats/caps, skills/titles acquired, lasting status effects, inventory/custody, named mechanics referenced as invariants.
   8:   - EPHEMERAL: roll results, damage numbers, overkill/comedic calculators, one-off warnings, momentary combat telemetry.
   9: - Enforce DURABLE claims against authoritative_surfaces/state/registries.
  10: - EPHEMERAL claims do not require state ownership; only flag EPHEMERAL contradictions inside the same scene as warnings.
  11: - UI gate:
  12:   - If scene_card.ui_allowed=false and any authoritative UI blocks appear, emit issue code 'ui_gate_violation' (severity depends on lint mode).
  13:   - If ui_allowed is missing and UI blocks appear, emit 'ui_gate_unknown' (warning) requesting explicit ui_allowed; do not fail solely for missing flag.
  14:   - Inline bracketed UI (e.g., [HP: 1/1]) is still UI and should be gated the same way; do not embed UI mid-sentence.
  15: - If uncertain, default to EPHEMERAL (warning at most), not DURABLE (error).
  16: - status="fail" only if there is at least one issue with severity="error"; warnings alone => status="pass".
  17: - Item naming enforcement scope:
  18:   - Do not require that every mention in narrative prose use display_name.
  19:   - Enforce canonical display_name for: (a) anchoring at first introduction (same paragraph or within the next 2 sentences),
  20:     (b) any custody-change sentence (drop/pick up/hand off/stow/equip/transfer), and (c) any case where a descriptor is ambiguous among multiple durable items in the scene.
  21:   - Otherwise, treat non-canonical descriptive references as warnings at most.
  22: - Prose hygiene: flag internal ids or container codes in narrative prose (CHAR_, ITEM_, THREAD_, DEVICE_, hand_left, hand_right).
  23: - Naming severity policy:
  24:   - warning: unambiguous descriptor used post-anchor.
  25:   - error: missing anchor, descriptor used during custody-change without canonical name, or ambiguity risk.
  26: 
  27: - Appearance enforcement (authoritative surface):
  28:   - APPEARANCE_CHECK is authoritative for cast_present_ids.
  29:   - Compare APPEARANCE_CHECK tokens to appearance_current atoms/marks (alias-aware).
  30:   - If APPEARANCE_CHECK contradicts appearance_current, emit error code "appearance_mismatch".
  31:   - Prose-only appearance contradictions are warnings unless explicitly durable and uncorrected in-scene.
  32:   - If prose depicts a durable appearance change but scene_card.durable_appearance_changes does not include it and no appearance_updates are present, emit error code "appearance_change_undeclared".
  33:   - If APPEARANCE_CHECK is missing for a cast member, emit warning code "appearance_check_missing".
  34: - For authoritative surfaces, prefer exact canonical item/device labels from registries.
  35: - For milestone repetition/future checks, compare against PRE-INVARIANTS only (pre-scene canon).
  36: - For ownership/consistency checks, compare against POST-STATE (post-patch candidate).
  37: - POST-STATE is canonical; character_states is a derived convenience view. If they contradict, emit pipeline_state_incoherent.
  38: - Check for POV drift vs book POV (no first-person in third-person scenes).
  39:   - Ignore first-person pronouns inside quoted dialogue; only narration counts.
  40: - Deterministically enforce scene-card durable constraints (required_in_custody, required_scene_accessible, forbidden_visible, device_presence; optional required_visible_on_page).
  41: - Durable constraint evaluation must use POST-STATE candidate (after patch), not pre-state.
  42: - Report missing durable context ids with explicit retry hints instead of guessing canon.
  43: - Input consistency check (mandatory, before issuing continuity/durable errors):
  44:   - If MUST_STAY_TRUE invariants contradict the provided post-patch candidate character state, treat this as an upstream snapshot error.
  45:   - In that case emit a single error issue with code "pipeline_state_incoherent" including evidence of the invariant and the conflicting state field.
  46:   - Do NOT emit additional continuity errors for the same fields when pipeline_state_incoherent is present.
  47: - must_stay_true removals:
  48:   - Lines starting with "REMOVE:" are deletion directives, not invariants.
  49:   - Ignore REMOVE lines when checking contradictions.
  50:   - If a REMOVE directive targets a fact, treat that fact as non-canonical even if it appears earlier in must_stay_true.
  51: - If pipeline_state_incoherent is present, issues MUST contain exactly one issue.
  52: - For each issue, include evidence when possible (line number + excerpt) as {"evidence": {"line": N, "excerpt": "..."}}.
  53: - Evaluate consistency over the full scope of the scene, not a single snapshot.
  54:   - Transitional state: a temporary mismatch later corrected or superseded within this scene.
  55:   - Durable violation: a mismatch that persists through the end of the scene or ends unresolved.
  56:   - You MUST read the entire scene and build a minimal timeline of explicit state claims/updates (UI lines, inventory changes, title/skill changes, location/time claims).
  57:   - If you detect an apparent inconsistency, you MUST search forward for later updates that resolve or supersede it.
  58:   - Only produce FAIL for durable violations. If resolved within the scene, do NOT FAIL; at most emit a warning.
  59:   - When the same stat appears multiple times, the last occurrence in the scene is authoritative unless an explicit rollback is stated.
  60:   - Any durability violation must cite both the conflicting line and the lack of later correction (or state "no later correction found").
  61: 
  62: Required keys:
  63: - schema_version ("1.0")
  64: - status ("pass" or "fail")
  65: - issues (array of objects)
  66: 
  67: Each issue object must include:
  68: - code
  69: - message
  70: Optional:
  71: - severity
  72: - evidence
  73: 
  74: If there are no issues, return:
  75: {
  76:   "schema_version": "1.0",
  77:   "status": "pass",
  78:   "issues": []
  79: }
  80: 
  81: If there are issues, return:
  82: {
  83:   "schema_version": "1.0",
  84:   "status": "fail",
  85:   "issues": [
  86:     {"code": "continuity", "message": "Example issue", "severity": "error"}
  87:   ]
  88: }
  89: 
  90: Scene:
  91: {{prose}}
  92: 
  93: Scene card:
  94: {{scene_card}}
  95: 
  96: Authoritative surfaces:
  97: {{authoritative_surfaces}}
  98: 
  99: Appearance check (authoritative):
 100: {{appearance_check}}
 101: 
 102: Character states (post-patch candidate, per cast_present_ids):
 103: {{character_states}}
 104: 
 105: Item registry (canonical):
 106: {{item_registry}}
 107: 
 108: Plot devices (canonical):
 109: {{plot_devices}}
 110: 
 111: Pre-state (before patch):
 112: {{pre_state}}
 113: 
 114: Pre-summary (facts-only):
 115: {{pre_summary}}
 116: 
 117: Pre-invariants (must_stay_true + key facts):
 118: {{pre_invariants}}
 119: 
 120: Post-state candidate (after patch):
 121: {{post_state}}
 122: 
 123: Post-summary (facts-only):
 124: {{post_summary}}
 125: 
 126: Post-invariants (must_stay_true + key facts):
 127: {{post_invariants}}
 128: 
 129: 
```
