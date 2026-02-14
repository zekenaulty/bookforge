# Validation Log - Prompt Composition

## Usage
- Track deterministic and behavioral validation runs.

## Entry Template
- timestamp:
- validation_type:
- command_or_method:
- baseline_reference:
- compared_reference:
- metrics:
- result:
- regressions_detected:
- follow_up:

## Entries

- timestamp: 2026-02-13T17:15:33-06:00
- validation_type: composition_contracts_and_determinism
- command_or_method: .venv/Scripts/python scripts/validate_prompt_composition.py
- baseline_reference: resources/prompt_composition/source_of_truth_checksums.json
- compared_reference: composed output from resources/prompt_composition/manifests/*.composition.manifest.json
- metrics: templates=14; checksum_enforcement=pass; determinism=pass; unknown_tokens=0; encoding_policy=utf8_no_bom_lf_pass
- result: pass
- regressions_detected: none
- follow_up: Execute behavioral regression suite (Story 5).

- timestamp: 2026-02-13T17:15:33-06:00
- validation_type: unit_tests_targeted
- command_or_method: .venv/Scripts/python -m pytest tests/test_prompt_composition.py tests/test_workspace_init.py -q
- baseline_reference: Existing workspace and prompt tests
- compared_reference: Post-composition implementation
- metrics: tests_run=7; tests_passed=7; tests_failed=0
- result: pass
- regressions_detected: none
- follow_up: Add CI wiring for scripts/validate_prompt_composition_controls.py with changed-file inputs.

- timestamp: 2026-02-13T17:15:33-06:00
- validation_type: control_log_enforcement
- command_or_method: .venv/Scripts/python scripts/validate_prompt_composition_controls.py --changed-file src/bookforge/prompt/composition.py --changed-file resources/prompt_composition/manifests/write.composition.manifest.json --changed-file resources/prompt_blocks/shared/summary/must_stay_true_end_state_rule.md
- baseline_reference: resources/plans/prompt_template_composition_forensics_20260213_183000/controls/*.md
- compared_reference: post-implementation control logs with populated entries
- metrics: required_logs=5; missing_logs=0; entry_field_completeness=pass
- result: pass
- regressions_detected: none
- follow_up: Keep script wired in CI and require changed-file arguments from git diff.

- timestamp: 2026-02-13T17:15:33-06:00
- validation_type: post-hardening_recheck
- command_or_method: .venv/Scripts/python -m pytest tests/test_prompt_composition.py tests/test_workspace_init.py -q; .venv/Scripts/python scripts/validate_prompt_composition.py
- baseline_reference: prior successful Story 0-4 validation run
- compared_reference: workspace copy-path hardening revision
- metrics: tests_run=7; tests_passed=7; composition_validation=pass
- result: pass
- regressions_detected: none
- follow_up: none (Story 5 remains pending).
