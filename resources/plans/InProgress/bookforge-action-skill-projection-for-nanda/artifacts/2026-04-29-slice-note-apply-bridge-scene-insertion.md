# Slice Note: Apply Bridge Scene Insertion Contract Hardening

Date: 2026-04-29

Repo: BookForge / `ai-book`

Owner: BookForge engine workstream

## Slice

Confirm and harden the BookForge side of `apply_bridge_scene_insertion` so Nanda can decide whether to wire or intentionally withhold it.

## Changed

- Clarified stale-write wording for scene/adaptive branch actions so branch-local stale targets are not described as "main-branch" drift.
- Added focused refusal tests for `apply_bridge_scene_insertion`.
- Expanded workflow help docs with Nanda integration contract details.
- Added contract handoff artifact for Nanda.

## Files Touched

- `src/bookforge/execution/scene_actions.py`
- `tests/test_adaptive_authoring_actions.py`
- `docs/help/workflow.md`
- `resources/plans/InProgress/bookforge-action-skill-projection-for-nanda/plan.md`
- `resources/plans/InProgress/bookforge-action-skill-projection-for-nanda/artifacts/2026-04-29-apply-bridge-scene-insertion-contract.md`

## Contract / Schema Notes

No schema field was renamed.

Confirmed public keys:

- static capability id: `action.apply_bridge_scene_insertion`
- legal/action key: `apply_bridge_scene_insertion`
- CLI: `bookforge workflow apply-bridge-scene-insertion`
- request builder: `build_apply_bridge_scene_insertion_request(...)`
- executor: `apply_bridge_scene_insertion_action(...)`

Confirmed success fields:

- `details.canonical_changed=false`
- `details.branch_change_status=changed`
- `details.inserted_scene_id`
- `details.recommended_next_actions=["plan_scene", "continue_scene"]`
- `artifact_paths.bridge_scene_insertion_apply_report`
- `artifact_paths.outline`
- `artifact_paths.snapshot_registry`

Confirmed failure codes:

- `branch_required`
- `missing_live_node`
- `stale_write`
- `scope_contract_violation`
- `bridge_scene_insertion_apply_failed`

## Validation

Command:

```powershell
python -m pytest tests/test_adaptive_authoring_actions.py -q
```

Result:

```text
13 passed in 16.15s
```

Coverage added:

- `main` branch apply refusal
- no adjacent scene legal-action refusal
- stale expected node refusal

## Nanda Reaction Needed

Please choose one state:

1. `wire_now`
   - use the contract artifact as the implementation target
   - gate behind route/scope projection, non-main branch, same-section adjacency, existing proposal, legal action, and receipt UI
2. `withhold_for_now`
   - mark as `implemented_upstream_withheld_in_nanda`
   - expose the withheld reason in action cards and author response context

Recommended first state: `wire_now`, because BookForge now has branch-only refusal, legal-action gating, stale target refusal, canonical unchanged receipt semantics, and focused tests for the key safety gates.

## Heartbeat Target Recommendation

Do not use `veiled_ledger_b1` for the first normal authoring heartbeat. It is the contaminated recovery target and currently has no derived branch inventory in this workspace.

Use a disposable healthy book/branch instead:

- book: `heartbeat_smoke_b1`
- branch: `heartbeat-ch1-sc1`
- scope: chapter `1`, section `1`, scene `1`
- first action: `continue_scene`
- loop: low max steps, non-main branch only

Use `veiled_ledger_b1` later for the recovery smoke path after route/scope truth and recovery action cards are in place.

