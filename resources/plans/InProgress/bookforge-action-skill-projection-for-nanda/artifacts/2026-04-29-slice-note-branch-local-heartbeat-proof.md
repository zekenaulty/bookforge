# Slice Note: Branch-Local Heartbeat Proof

Date: 2026-04-29

Repo: BookForge / `ai-book`

Owner: BookForge engine workstream

## Slice

Add a focused BookForge regression for the first branch-local authoring heartbeat shape Nanda is preparing to smoke test.

The target invariant:

```text
derived branch + selected scene
  -> continue_scene
  -> one recommended child action
  -> receipt/artifact refs
  -> branch-local artifact visible
  -> canonical main untouched
```

## Change

Added regression coverage:

- `test_continue_scene_branch_local_heartbeat_preserves_main_and_exposes_artifacts`

The test:

1. creates a healthy one-section book
2. freezes the section
3. creates a derived authoring branch
4. runs one `continue_scene` step on that branch
5. verifies the child action is `plan_scene`
6. verifies `canonical_changed=false`
7. verifies branch execution results include both child and wrapper receipts
8. verifies the scene card exists only in the branch snapshot
9. verifies branch artifact index and diff expose the branch-only artifact
10. verifies `get_next_writing_target(...)` still recommends `continue_scene` with the next scene-phase action

## Artifact Classification Tightening

While adding the heartbeat regression, BookForge tightened branch artifact classification:

- `draft/context/phase_history/<scope>/<artifact>.json`
  - `artifact_class=scene_phase_artifact`
  - `artifact_status=provisional`
- `draft/context/phase_history/<scope>.json`
  - `artifact_class=scene_phase_history`
  - `artifact_status=diagnostic`

This aligns branch artifact indexes with scene-phase execution receipts. Nanda can use the artifact index without treating all phase-history files as generic derived context.

## Validation

Focused command:

```powershell
python -m pytest tests/test_scene_action_execution.py::test_continue_scene_branch_local_heartbeat_preserves_main_and_exposes_artifacts -q
```

Result:

```text
1 passed
```

## Nanda Consumption Note

For the controlled heartbeat smoke:

- use a non-main branch
- run one `continue_scene`
- expect `author_loop_step_receipt_v1`
- expect `canonical_changed=false`
- refresh branch artifact index and diff from BookForge
- do not derive artifact status from path names in React
- treat `scene_phase_artifact` records as provisional execution outputs
