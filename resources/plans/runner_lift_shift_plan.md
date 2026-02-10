# Runner Lift-and-Shift Refactor Plan (No Logic Changes)

## Goal
Extract `runner.py` into small modules with zero behavior change. Only move code and update imports.

## Constraints
- Do not change logic, signatures, names, or call order.
- No renames or data shape changes.
- Run tests after each phase.

## Status
- Phase 0: baseline complete (pytest -q)
- Phase 1: parse module extracted (complete)
- Phase 2: complete (prompts module extracted)
- Phase 3: complete (llm_ops extracted)
- Phase 4: complete (lint tripwires extracted)
- Phase 5: complete (state_patch extracted)
- Phase 6: complete
- Phase 7: complete
- Phase 8: complete


## Phase 0: Safety Baseline
- Run `pytest -q` and record pass status.
- Note current `runner.py` public entry points (e.g., `run_loop`, CLI usage).

## Phase 1: Pure Parsing/Extraction (low risk)
**New module:** `src/bookforge/pipeline/parse.py`

**Move as-is:**
- `_extract_json`
- `_extract_prose_and_patch`
- `_extract_authoritative_surfaces`
- `_extract_ui_stat_lines`
- `_find_first_match_evidence`
- `_strip_dialogue`

**Runner changes:** import these from `pipeline.parse`.

**Tests:** full suite.

## Phase 2: Prompt/Template Resolution (low risk)
**New module:** `src/bookforge/pipeline/prompts.py`

**Move as-is:**
- `_resolve_template`
- `_system_prompt_for_phase`

**Runner changes:** import from `pipeline.prompts`.
**Note:** `render_template_file` remains in `bookforge.prompt.renderer`.

**Tests:** full suite.

## Phase 3: LLM Call Wrapper (low risk)
**New module:** `src/bookforge/pipeline/llm_ops.py`

**Move as-is:**
- `_chat`
- `_response_truncated`
- `_json_retry_count`
- `_state_patch_schema_retry_message`
- `_lint_status_from_issues` (if not in lint merge)

**Runner changes:** import from `pipeline.llm_ops`.

**Tests:** full suite.

## Phase 4: Lint Tripwires (medium-low risk)
**New package:** `src/bookforge/pipeline/lint/`

**Move as-is:**
- `_stat_mismatch_issues`
- `_pov_drift_issues`
- `_heuristic_invariant_issues`
- `_durable_scene_constraint_issues`
- `_linked_durable_consistency_issues`
- `_lint_has_issue_code`
- `_lint_issue_entries`
- `_lint_status_from_issues` (if not already in llm_ops)

**Runner changes:** import from `pipeline.lint.tripwires` (and `pipeline.lint.merge` if split).

**Tests:** lint-related tests, then full suite.

## Phase 5: State Patch Normalization (medium risk)
**New module:** `src/bookforge/pipeline/state_patch.py`

**Move as-is:**
- `_normalize_state_patch_for_validation`
- `_sanitize_preflight_patch`
- `_coerce_summary_update`
- `_coerce_character_updates`
- `_coerce_stat_updates`
- `_coerce_transfer_updates`
- `_coerce_inventory_alignment_updates`
- `_coerce_registry_updates`
- `_fill_character_update_context`
- `_fill_character_continuity_update_context`
- `_migrate_numeric_invariants`

**Runner changes:** import from `pipeline.state_patch`.

**Tests:** state_patch tests, then full suite.

## Phase 6: State Apply (medium risk)
**New module:** `src/bookforge/pipeline/state_apply.py`

**Move as-is:**
- `_apply_state_patch`
- `_apply_character_updates`
- `_apply_character_stat_updates`
- `_apply_character_continuity_system_updates`
- `_apply_global_continuity_system_updates`
- `_apply_run_stat_updates`
- `_update_bible`
- `_rollup_chapter_summary`
- `_compile_chapter_markdown`

**Runner changes:** import from `pipeline.state_apply`.

**Tests:** full suite.

## Phase 7: Durable State Ops (medium-high risk)
**New module:** `src/bookforge/pipeline/durable.py`

**Move as-is:**
- `_durable_state_context`
- `_apply_durable_updates_or_pause`
- `_durable_mutation_payload`
- `_enforce_scope_policy`
- `_plot_device_update_is_intangible`
- `_scope_override_enabled`
- `_reason_category`
- `_block_touches_physical_keys`
- Durable helper fns used only by the above (e.g., `_derive_item_scene_flags`, `_derive_plot_device_scene_flags`)

**Runner changes:** import from `pipeline.durable`.

**Tests:** durable tests, then full suite.

## Phase 8: Filesystem/Workspace Utilities (medium risk)
**New module:** `src/bookforge/pipeline/io.py`

**Move as-is:**
- `_load_json`
- `_write_scene_files`
- `_snapshot_character_states_before_preflight`
- `_log_scope`

**Runner changes:** import from `pipeline.io`.

**Tests:** full suite.

## Sequencing Rule
One phase per turn if needed; no logic changes, only moves/imports.

## Definition of Done
- `runner.py` is orchestration-only.
- All tests pass after each phase.
- No behavior change in logs/output.







