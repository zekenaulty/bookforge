# Pipeline State Incoherence Snapshot Fix Plan

## Metadata
- Timestamp: 2026-02-13 05:05:15
- Driver report: `resources/plans/ch1_phase_issue_audit_report_20260213_050515.md`
- Scope: fix only invalid mechanical `pipeline_state_incoherent` failures observed in:
  - `ch001_sc001` (stale wallet invariant in lint candidate)
  - `ch001_sc008` (stale Vane `back_sheath` invariant coexisting with `hand_right`)

## Objective
Eliminate false `pipeline_state_incoherent` failures caused by stale character invariant strings in lint candidate snapshots and persisted character state files, while preserving true incoherence detection.

## Non-Goals
- Do not relax real continuity enforcement.
- Do not change POV drift behavior.
- Do not redesign invariant schema in this pass.
- Do not change prompt text in this plan; this is mechanical/code alignment only.

## Root-Cause Summary (Verified)
1. `src/bookforge/pipeline/lint/helpers.py` (`_merged_character_states_for_lint`) merges character updates, but does **not** apply summary-level `REMOVE:` directives to `merged_state.invariants`.
2. Persisted apply path in `src/bookforge/pipeline/state_apply.py` removes only explicitly listed `REMOVE:` targets. If writer/state_repair misses a REMOVE for stale inventory posture, conflicting invariants can persist (scene 8 Vane case).
3. Result: lint candidate and/or persisted character state can contain contradictory inventory invariants even when inventory/containers and summary canonical facts are correct.
4. `summary_update.key_facts_ring_add` is coerced by `state_patch`, but state summary merge/removal logic is driven by `summary_update.must_stay_true`; this fix must align with currently effective channels, not assumed channels.

## Change Strategy
Treat summary inventory lines as hints and **structured inventory/containers as authority**. Reconcile only when summary and structured truth agree.

- Layer 1: Apply explicit removals (`REMOVE:`) from `summary_update.must_stay_true` in lint candidate merge (same semantics as persisted apply).
- Layer 2: Reconcile conflicting `inventory:` invariants only when canonical summary lines are corroborated by structured inventory/container state.
- Layer 3: Apply same guarded reconciliation in persisted character apply path to prevent stale invariant accumulation.
- Layer 4: Run reconciliation as the final invariant normalization step (after additions), so later merges cannot reintroduce stale lines.

## Detailed Stories

### Story 1: Lint Candidate Invariant Reconciliation
Status: `pending`

#### Touchpoints
- `src/bookforge/pipeline/lint/helpers.py`
  - `_merged_character_states_for_lint(...)`

#### Planned Changes
1. Parse summary removals from patch:
- Read `patch.summary_update.must_stay_true` (effective channel for invariant removal in current code).
- Split `REMOVE:` directives using existing semantics from `state_apply` (`_split_invariant_removals`).

2. Apply removals to candidate invariants:
- If `merged_state.invariants` is a list, apply `_apply_invariant_removals` before prompt/render paths and before deterministic incoherence checks run.

3. Add guarded inventory invariant reconciliation step:
- Build canonical inventory fact map from summary `must_stay_true` inventory lines (non-REMOVE only).
- Canonical selection rule: for repeated lines for same `subject + item_label`, last occurrence wins.
- Corroboration guardrail (required): only reconcile a canonical summary line if it is consistent with merged structured state (`inventory` + `containers`) for that character.
- For each character state:
  - Remove stale inventory invariant lines that conflict with corroborated canonical facts for the same `subject + item_label`.
  - Re-add canonical line (if missing) for the item/character represented in summary.

4. Define conflict deterministically:
- Conflict is only for lines parsed as `inventory:` with matching `subject + item_label` and differing any of:
  - `owner_scope/subject`
  - `status`
  - `container`
- Do not reconcile non-`inventory:` invariant lines in this story.

#### Why this fixes observed failures
- Scene 1 wallet: explicit REMOVE now applied to lint candidate invariants.
- Scene 8 sword posture: stale `back_sheath` line removed/replaced by canonical `hand_right` line even when REMOVE is absent.
- Guardrail protection: if summary and structured state disagree, reconciliation is skipped so true incoherence remains detectable.

#### Acceptance Criteria
- Candidate `character_states[].invariants` in lint prompt no longer includes stale wallet carried line in scene1-like payloads.
- Candidate `character_states[].invariants` no longer contains both `back_sheath` and `hand_right` for same Vane sword posture in scene8-like payloads.

---

### Story 2: Persisted Character Invariant Reconciliation
Status: `pending`

#### Touchpoints
- `src/bookforge/pipeline/state_apply.py`
  - `_apply_character_updates(...)`
  - likely helper additions near `_split_invariant_removals` / `_apply_invariant_removals`

#### Planned Changes
1. Keep existing explicit REMOVE handling.

2. Add reconciliation pass in `_apply_character_updates` as a **final invariant normalization step** (after inventory/container assignment and after `invariants_add` merge):
- Use summary canonical inventory facts from `must_stay_true` only.
- For the current character:
  - remove conflicting stale inventory invariants for corroborated canonical items.
  - ensure corroborated canonical inventory invariant lines are present.

3. Preserve current dedupe behavior and history recording, with final dedupe after reconciliation.

#### Why this is required
- Prevents stale invariant strings from persisting into future scenes and re-triggering incoherence later.
- Fixes scene8 class at source, not only at lint-candidate view.

#### Acceptance Criteria
- Persisted character state for Vane-like transition does not retain obsolete `back_sheath` invariant when inventory is now `hand_right`.
- Existing HP invariant removal behavior continues to pass (`tests/test_character_invariants_remove.py`).

---

### Story 3: Regression Tests (Focused)
Status: `pending`

#### Touchpoints
- `tests/test_lint_helpers.py`
- `tests/test_character_invariants_remove.py`

#### Planned Tests
1. `test_merged_character_states_applies_summary_remove_to_invariants`
- Input includes stale invariant and summary `REMOVE:`.
- Assert merged lint candidate invariants drop stale line.

2. `test_merged_character_states_reconciles_inventory_posture_without_remove`
- Input includes both old/new posture invariant lines for same item.
- Summary canonical line contains only new posture.
- Assert merged lint candidate contains only canonical line.

3. `test_apply_character_updates_reconciles_conflicting_inventory_invariants`
- Persisted character starts with stale posture invariant.
- Patch updates inventory posture but omits explicit REMOVE.
- Summary canonical inventory line present.
- Assert persisted invariants reflect only canonical posture.

4. `test_reconciliation_skips_when_summary_conflicts_with_structured_state`
- Summary line disagrees with structured inventory/container truth.
- Assert reconciliation does not overwrite invariants to match summary; incoherence remains visible.

5. Keep and run existing:
- `test_character_invariants_remove_from_summary` (must remain green).

#### Acceptance Criteria
- New tests pass.
- Existing invariant-removal tests pass unchanged.
- Safety test confirms we do not convert true state bugs into false passes.

---

### Story 4: Verification Against Real Incident Shape
Status: `pending`

#### Method
Use synthetic tests to mirror incident payloads from:
- `workspace/logs/llm/criticulous_b1_ch001_sc001_lint_scene_20260213_080554.prompt.txt`
- `workspace/logs/llm/criticulous_b1_ch001_sc008_lint_scene_20260213_102259.prompt.txt`

#### Verification Targets
- Wallet custody conflict is normalized out before lint incoherence gate.
- Vane sword dual-posture invariant conflict is normalized out before lint incoherence gate.
- Summary-vs-structured disagreement remains detectable as incoherence.

#### Note
No expensive full scene rerun is required to prove the mechanical fix at this stage; regression tests should model exact conflict payload shape.

## Exact Code Areas to Modify
- `src/bookforge/pipeline/lint/helpers.py`
  - Add summary removal extraction from patch summary update.
  - Add guarded inventory invariant reconciliation call(s) inside `_merged_character_states_for_lint`.
- `src/bookforge/pipeline/state_apply.py`
  - Add helper(s) to parse inventory invariant lines and reconcile character invariant lines using structured-state corroboration.
  - Invoke reconciliation inside `_apply_character_updates` as late final invariant normalization.
- `tests/test_lint_helpers.py`
  - Add targeted tests for summary-remove, posture reconciliation, and summary-vs-structured safety.
- `tests/test_character_invariants_remove.py`
  - Add one targeted persisted-state posture reconciliation test.

## Risks and Mitigations

### Risk 1: Over-removal of legitimate invariants
- Scenario: two distinct items share similar labels.
- Mitigation:
  - Reconcile only lines parsed as `inventory:` invariants.
  - Match by normalized full item label token from invariant grammar, not fuzzy substring.

### Risk 2: Item label normalization mismatch
- Scenario: canonical summary uses different alias than character invariant line.
- Mitigation:
  - Keep exact-match reconciliation as baseline.
  - If no match, do no-op (avoid destructive guessing).

### Risk 3: Transitional duplicate lines in summary itself
- Scenario: summary contains both old and new lines in same patch.
- Mitigation:
  - Apply `last occurrence wins` only after structured-state corroboration.

### Risk 4: Reconciliation removes non-inventory invariants
- Mitigation:
  - Restrict logic to lines starting with `inventory:`.

### Risk 5: Behavior drift between lint candidate and persisted apply paths
- Mitigation:
  - Implement shared helper logic (single source of truth) or mirror tests for both code paths.

### Risk 6: Circular import / helper placement issues
- Mitigation:
  - Keep reconciliation helpers in `state_apply.py` (already imported by lint helpers), or create a neutral utility module if needed.

### Risk 7: Summary text incorrectly treated as authority
- Scenario: summary line is wrong/out-of-order.
- Mitigation:
  - Structured inventory/containers remain authority.
  - Skip reconciliation when summary cannot be corroborated.

## Edge Cases Checklist
- Same item transitions owner (`CHAR_ARTIE` -> `world`) without explicit REMOVE.
- Same item transitions container/status (`back_sheath equipped` -> `hand_right held`) without explicit REMOVE.
- Summary includes canonical inventory line but no `character_updates.invariants_add`.
- Summary has REMOVE directives in `must_stay_true` (effective path).
- `key_facts_ring_add` contains inventory text (should not drive this fix unless code path later starts consuming it).
- Character state invariants list missing or malformed (non-list).
- Multiple inventory lines for same item in one summary payload (ensure last one canonical).
- Case/spacing differences in invariant strings.
- Summary canonical line present but disagrees with structured inventory/containers (must skip reconciliation).

## Definition of Done
1. Scene1-type stale wallet invariant conflict is normalized out in lint candidate merge.
2. Scene8-type dual posture invariant conflict is normalized out in lint candidate merge and persisted character state apply.
3. New regression tests pass and existing invariant removal tests remain green.
4. No regressions in lint helper continuity update tests.
5. Safety scenario proves real incoherence is not auto-normalized away.

## Status Tracker
- Story 1: Lint Candidate Invariant Reconciliation -> `completed`
- Story 2: Persisted Character Invariant Reconciliation -> `completed`
- Story 3: Regression Tests -> `completed`
- Story 4: Incident-Shape Verification -> `completed`

## Execution Notes
- Run tests with repo venv and correct working directory.
- Suggested command:
  - `\.venv\Scripts\python -m pytest tests/test_lint_helpers.py tests/test_character_invariants_remove.py -q`


## Execution Log
- Implemented shared inventory invariant parsing/reconciliation helpers in `src/bookforge/pipeline/state_apply.py`:
  - `_parse_inventory_invariant`
  - `_canonical_inventory_invariants`
  - `_inventory_matches_posture`
  - `_reconcile_inventory_invariants`
- Updated persisted apply flow in `_apply_character_updates` to:
  - extract summary removals/canonical inventory facts from `summary_update.must_stay_true`
  - apply guarded reconciliation as final invariant normalization after `invariants_add` merge.
- Updated lint candidate merge in `src/bookforge/pipeline/lint/helpers.py` to:
  - merge `invariants_add` into `invariants` for candidate realism
  - apply summary `REMOVE:` directives to candidate invariants
  - apply guarded inventory invariant reconciliation before lint prompt assembly.
- Added tests:
  - `tests/test_lint_helpers.py`
    - `test_merged_character_states_applies_summary_remove_to_invariants`
    - `test_merged_character_states_reconciles_inventory_posture_without_remove`
    - `test_reconciliation_skips_when_summary_conflicts_with_structured_state`
  - `tests/test_character_invariants_remove.py`
    - `test_apply_character_updates_reconciles_conflicting_inventory_invariants`

## Verification Evidence
- Ran targeted suite:
  - `\.venv\Scripts\python -m pytest tests/test_lint_helpers.py tests/test_character_invariants_remove.py -q`
  - Result: `7 passed`
- Ran broader regression subset:
  - `\.venv\Scripts\python -m pytest tests/test_state_summary.py tests/test_state_rollups.py tests/test_lint_helpers.py tests/test_character_invariants_remove.py -q`
  - Result: `12 passed`

## New Concerns Discovered
- Conservative guardrail behavior: reconciliation requires an existing corroborated invariant line for the same subject+item+posture.
  - Benefit: avoids converting true incoherence into false pass.
  - Tradeoff: if only stale lines exist and no corroborated line is present (and no explicit `REMOVE:`), stale invariant cleanup will not auto-fire.
- Current reconciliation scope is intentionally limited to `summary_update.must_stay_true`.
  - If future flows depend on inventory facts in `key_facts_ring_add`, this logic would need explicit extension.
- Summary lines with `subject=world` are only handled via explicit `REMOVE:` against character invariants (by design in this pass).

