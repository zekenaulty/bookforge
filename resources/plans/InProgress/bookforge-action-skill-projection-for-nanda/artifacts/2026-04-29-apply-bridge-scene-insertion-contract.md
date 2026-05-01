# Apply Bridge Scene Insertion Contract Confirmation

Date: 2026-04-29

Slice: `apply_bridge_scene_insertion` reconciliation

Owner: BookForge engine workstream

Nanda counterpart ask:

- Decide whether to wire this action now or mark it `implemented_upstream_withheld_in_nanda`.
- Use this note as the BookForge contract reference for route/scope capability projection and action-card gating.

## Contract Status

BookForge considers the current same-section branch-local implementation product-safe enough for Nanda to wire behind gates.

Scope of that statement:

- same-section adjacent scene pairs only
- derived branch only
- existing bridge-scene insertion proposal required
- no prose generation
- no canonical mutation
- no cross-section insertion
- no promotion

This action materializes the structural decision that a new bridge scene is needed. It does not complete the bridge scene. After apply, Nanda/author should use the normal scene-phase graph on the inserted scene:

1. `plan_scene`
2. `preflight_scene_state`
3. `generate_continuity_pack`
4. `write_scene_prose`
5. `state_repair_scene_patch`
6. `lint_scene_prose`
7. `repair_scene_prose` as needed
8. `apply_scene_commit`
9. seam alignment as needed

## Public Keys

- Static capability id: `action.apply_bridge_scene_insertion`
- Legal/action key: `apply_bridge_scene_insertion`
- Request builder: `bookforge.execution.build_apply_bridge_scene_insertion_request(...)`
- Executor: `bookforge.execution.apply_bridge_scene_insertion_action(...)`
- CLI: `bookforge workflow apply-bridge-scene-insertion`
- Dynamic legality source:
  - `bookforge.query.list_execution_options(...)`
  - `bookforge workflow legal-actions ... --json`

## Selector Shape

Required:

- `book_id`
- `branch_id`
- `chapter`
- `scene` / `scene_a_id`

Optional:

- `scene_b_id`
- `section`
- `bridge_plan_path`

Rules:

- `branch_id` must not be `main`.
- `scene_a_id` must have an adjacent next scene in the selected branch outline.
- `scene_b_id`, if provided, must match the adjacent next scene.
- The matching bridge-scene insertion plan must exist in the same branch and same pair.

## Legal Action Details

When selected through `list_execution_options(...)`, the action returns detail fields including:

- `chapter_id`
- `scene_a_id`
- `scene_b_id`
- `mutation_scope=branch_authoritative`
- `artifact_status_after_success=authoritative`
- `canonical_changed=false`
- `renumbering_policy=branch_local_shift_following_integer_scene_ids`
- `same_section_only=true`
- `bridge_plan_path` when a candidate pair exists
- `refusal_code` when blocked

Allowed only when:

- branch is derived
- chapter/scene scope is present
- adjacent next scene exists
- matching bridge-scene insertion plan exists

## Success Result

Expected `ExecutionResult`:

- `status=success`
- `action=apply_bridge_scene_insertion`
- `details.inserted_scene_id=<new scene id>`
- `details.branch_id=<branch id>`
- `details.canonical_changed=false`
- `details.branch_change_status=changed`
- `details.recommended_next_actions=["plan_scene", "continue_scene"]`
- `artifact_paths.bridge_scene_insertion_apply_report`
- `artifact_paths.outline`
- `artifact_paths.snapshot_registry`

Produced artifact receipts:

- `bridge_scene_insertion_apply_report`
  - label: `Bridge scene insertion apply report`
  - artifact status: `diagnostic`
  - format: `application/json`
  - consumable: `true`
  - resumable: `false`
  - replaceable: `true`
- `branch_outline`
  - label: `Branch outline after bridge insertion`
  - artifact status: `authoritative`
  - format: `application/json`
  - details include `branch_authoritative=true`
- `branch_snapshot_registry`
  - label: `Branch snapshot registry after bridge insertion`
  - artifact status: `authoritative`
  - format: `application/json`
  - details include `branch_authoritative=true`

Apply report payload:

- `schema_version=bridge_scene_insertion_apply_report_v1`
- `book_id`
- `branch_id`
- `chapter_id`
- `section_id`
- `scene_a_id`
- `scene_b_id`
- `inserted_scene_id`
- `status=applied`
- `artifact_status=diagnostic`
- `source_bridge_plan`
- `ref_map`
- `moved_artifacts`
- `rebuilt_views`
- `recommended_next_actions`
- `created_at`

## Mutation Semantics

Successful apply:

- inserts a provisional bridge scene into branch-local `outline/outline.json`
- updates branch-local `outline/snapshot_registry.json`
- rebuilds branch-local outline projections
- shifts following branch-local integer scene artifacts
- records moved artifacts in the apply report
- advances the branch current node to `phase_id=apply_bridge_scene_insertion`
- leaves canonical `main` unchanged
- leaves bridge prose unwritten

The inserted outline scene includes:

- `introduced_by=apply_bridge_scene_insertion`
- `insertion_status=provisional`
- `source_bridge_plan`
- `source_scene_pair`
- constraints requiring preservation of scene A's ending and scene B's established facts/outcome

## Refusal And Failure Semantics

Legal-action refusal reasons:

- `apply_bridge_scene_insertion requires a derived branch; bridge insertion is branch-local.`
  - `details.refusal_code=branch_required`
- `apply_bridge_scene_insertion requires chapter and scene scope.`
  - `details.refusal_code=missing_chapter_or_scene_scope`
- `No adjacent next scene exists in the selected chapter outline.`
  - `details.refusal_code=no_adjacent_scene`
- `apply_bridge_scene_insertion requires an existing bridge scene insertion plan.`
  - `details.refusal_code=missing_bridge_scene_insertion_plan`

Execution failure codes:

- `branch_required`
  - direct execution on `main`
- `missing_live_node`
  - no current execution node for the selected branch
- `stale_write`
  - expected node revision was superseded by a newer execution revision
- `scope_contract_violation`
  - live node scope does not match expected node scope
- `bridge_scene_insertion_apply_failed`
  - missing/mismatched bridge plan
  - unsupported plan shape
  - non-adjacent active outline pair
  - failed branch-local artifact materialization

All failure results include:

- `status=hard_fail`
- `details.canonical_changed=false`
- selected scope details
- `details.failure_code`

## Nanda Gating Recommendation

Nanda should expose this action only when all are true:

1. route/scope projection is branch-live
2. `branch_id != "main"`
3. `book_id`, `chapter`, and `scene` are selected
4. branch detail/legal actions show `apply_bridge_scene_insertion.allowed=true`
5. bridge proposal evidence is present
6. selected pair is same-section adjacent
7. expected receipt type is accepted by Nanda
8. user/author has explicitly selected "apply" after seeing the proposal

Suggested user-facing label:

`Insert planned bridge scene on branch`

Suggested blocked state if Nanda withholds despite upstream support:

`Implemented in BookForge, withheld in Nanda until route/scope action cards and apply-receipt UI are wired.`

## Heartbeat Smoke Target Recommendation

Current workspace inspection found:

- `workspace/books/veiled_ledger_b1`
- no existing derived branch inventory under that book
- `veiled_ledger_b1` is the known contaminated/chimera book and should be reserved for recovery-path testing, not the first authoring heartbeat.

Recommendation:

Use a disposable healthy smoke book for the first heartbeat test, not `veiled_ledger_b1`.

Suggested target shape:

- book id: `heartbeat_smoke_b1`
- branch id: `heartbeat-ch1-sc1`
- scope: chapter `1`, section `1`, scene `1`
- first action: `continue_scene`
- loop envelope: low max steps, non-main branch only

If Nanda needs to test against the current real workspace before creating a new book, first create a derived branch from a known healthy book state. Do not use Veiled Ledger's contaminated main as proof that the normal author loop is healthy.

Veiled Ledger should be the recovery smoke target after the route/scope truth path is closed:

- diagnose lineage
- select anchor
- create recovery branch
- run one branch-local recovery step
- inspect receipts/diff
- do not promote until validation-first UI exists

## Validation

Focused BookForge validation:

```powershell
python -m pytest tests/test_adaptive_authoring_actions.py -q
```

Result:

```text
13 passed in 16.15s
```

New/refined coverage:

- success applies branch-local bridge insertion and shifts artifacts
- direct `main` execution refuses with `branch_required`
- legal action blocks when no adjacent pair exists
- stale expected node refuses with `stale_write`
- missing bridge proposal remains blocked by legal action
