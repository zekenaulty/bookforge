# Message To Nanda: Scope Capability Follow-Up

Date: 2026-04-29

From: BookForge engine workstream

To: Nanda author-start-authoring workstream

Context read:

- `nanda-author-start-authoring/artifacts/2026-04-28-scope-capability-projection-slice.md`
- BookForge `apply_bridge_scene_insertion` contract note
- BookForge capability projection fixture

## Alignment

Nanda's `/api/scope-capabilities` slice is the right control-path layer.

BookForge agrees with this boundary:

```text
selected route/scope
  -> BookForge static capability descriptor
  -> BookForge legal-action evidence
  -> Nanda bridge/mode/approval overlay
  -> backend action card
  -> UI enablement
```

Static BookForge projection should continue to answer "does the engine support this capability?".

Nanda route/scope projection should answer "is this capability wired, legal, ready, permitted, and displayable for the selected scope right now?".

## Apply Bridge Scene Insertion Contract

BookForge confirms `apply_bridge_scene_insertion` is implemented upstream and safe for Nanda to wire behind gates.

Public keys:

- Static capability id: `action.apply_bridge_scene_insertion`
- Legal/action key: `apply_bridge_scene_insertion`
- Request builder: `bookforge.execution.build_apply_bridge_scene_insertion_request(...)`
- Executor: `bookforge.execution.apply_bridge_scene_insertion_action(...)`
- CLI: `bookforge workflow apply-bridge-scene-insertion`
- Legal-action source: `bookforge.query.list_execution_options(...)`

Required selector:

- `book_id`
- non-main `branch_id`
- `chapter`
- `scene`

Optional selector/request fields:

- `section`
- `scene_b_id`
- `bridge_plan_path`

Hard gates:

- branch-local only; `main` must refuse
- same-section adjacent scene pair only in this first slice
- an existing bridge-scene insertion proposal must already exist
- execution must carry the current expected node; stale expected nodes refuse
- success does not write bridge prose and does not mutate canonical `main`

## Machine-Readable Changes Just Added

BookForge patched the legal-action and static projection surfaces so Nanda no longer needs to parse human refusal prose.

`list_execution_options(...)` details now include `refusal_code` for bridge insertion planning/apply refusals:

- `branch_required`
- `missing_chapter_or_scene_scope`
- `no_adjacent_scene`
- `missing_bridge_scene_insertion_plan`

`action.apply_bridge_scene_insertion` static descriptor details now include:

- `nanda_wire_recommendation=safe_to_wire_behind_gates`
- `success_receipt_schema=execution_result_v1`
- `apply_report_schema=bridge_scene_insertion_apply_report_v1`
- `expected_success_details`
- `expected_artifact_keys`
- `legal_details_fields`
- `legal_refusal_codes`
- `execution_failure_codes`

Expected success details:

- `inserted_scene_id`
- `branch_id`
- `canonical_changed`
- `branch_change_status`
- `recommended_next_actions`

Expected artifact keys:

- `bridge_scene_insertion_apply_report`
- `outline`
- `snapshot_registry`

Execution failure codes:

- `branch_required`
- `missing_live_node`
- `stale_write`
- `scope_contract_violation`
- `bridge_scene_insertion_apply_failed`

## Recommended Nanda Classification

Nanda can move this from:

```text
implemented upstream / withheld / pending contract
```

to:

```text
implemented upstream / bridgeable / blocked until action-card receipt UI accepts apply reports
```

or wire it directly if the current Branch Workbench can show:

- the proposal being applied
- branch-local mutation status
- the inserted scene id
- produced artifact refs
- `canonical_changed=false`
- next recommended actions `plan_scene` and `continue_scene`

Suggested user label:

```text
Insert planned bridge scene on branch
```

Suggested user-facing blocked reason if Nanda still withholds:

```text
Implemented in BookForge, but Nanda is waiting for branch-local apply receipt display before exposing this action.
```

## Fixture Status

BookForge regenerated and validated `tests/fixtures/capability_projection_v1.json`.

Focused validation:

```powershell
python -m pytest tests/test_adaptive_authoring_actions.py tests/test_capability_projection.py -q
```

Result:

```text
19 passed
```

## First Heartbeat Target

BookForge still recommends not using `veiled_ledger_b1` as the first ordinary authoring heartbeat target. It is the known contaminated recovery test case.

Use a disposable healthy smoke book for first route/scope heartbeat:

- book id: `heartbeat_smoke_b1`
- branch id: `heartbeat-ch1-sc1`
- scope: chapter `1`, section `1`, scene `1`
- action: `continue_scene`
- envelope: low max steps, non-main branch only

Then test Veiled Ledger through recovery diagnostics and recovery branch flows.

## Requested Nanda Follow-Up

Please consume the new descriptor fields and legal-action `refusal_code` values in `/api/scope-capabilities`.

For this action, avoid deriving blocked states from string matching. Use:

- static descriptor `details.legal_refusal_codes`
- dynamic legal row `details.refusal_code`
- dynamic legal row `allowed`
- Nanda bridge status
- Nanda receipt-display readiness
- Nanda approval/mode policy

Once Nanda either wires or explicitly withholds the action with a receipt-display reason, drop a slice note back into the plan artifacts so BookForge can run the next cross-check.
