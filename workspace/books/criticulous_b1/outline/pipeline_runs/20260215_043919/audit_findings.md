# Outline Rerun Audit - 20260215_043919

## Execution
- Command: `bookforge outline generate --book criticulous_b1 --rerun --force-rerun-with-draft --strict-transition-bridges --strict-location-identity`
- Result: failed at `phase_03_scene_draft` after 2 attempts

## Key Findings
- Phase 01 and 02 passed; phase 03 failed schema validation (`161` errors).
- Transition/location contract adoption succeeded in phase 03 output: all scenes include `location_start_id`, `location_end_id`, `handoff_mode`, `transition_in_text`; no placeholder-like location values detected.
- Remaining failures are core outline v1.1 schema omissions (chapter metadata + scene summary/characters + section intent).
- Retry appears to fix only the first validator error per attempt, leaving large residual error sets within the 2-attempt cap.
- No `outline_pipeline_report.json` was emitted on this failed run (visibility gap for failure mode).

## Metrics
- chapter_count: 7
- section_count: 19
- scene_count: 46
- scene_missing_location_ids: 0
- scene_invalid_location_id_pattern: 0
- scene_placeholder_location_values: 0
- scene_missing_transition_in_text: 0
- scene_missing_handoff_mode: 0
- scene_bad_ref_format: 0
- schema_error_count: 161

## Artifacts
- `phase_history.json`
- `phase_03_validation.json`
- `phase_03_output.json`
- `audit_phase_03_schema_errors.json`
