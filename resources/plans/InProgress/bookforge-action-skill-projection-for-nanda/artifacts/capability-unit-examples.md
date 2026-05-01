# Capability Unit Examples

Date: 2026-04-27

## Purpose
This artifact gives concrete examples of what should and should not become projected BookForge capabilities. It is meant to keep future command/skill extraction aligned with author intent instead of code convenience.

## Rule Of Thumb
Expose a capability when the author agent or operator can reasonably choose it as the next move.

Do not expose implementation helpers that only exist to complete a larger move.

## Scene Writing Units

### Public Primitive: `plan_scene`
Why public:
- It creates or refreshes a provisional scene card.
- The caller may want to inspect or revise the plan before prose.
- It has scene scope, readiness, receipt, artifact status, and refusal conditions.

Not public helpers:
- prompt rendering for scene plan
- provider retry wrapper
- JSON extraction
- schema fallback parser

### Public Primitive: `write_scene_prose`
Why public:
- The user explicitly wants to write prose without automatically linting/repairing/committing.
- It produces visible prose artifacts.
- It should be branch-local or provisional unless committed.

Receipt must say:
- branch or main
- canonical change status
- produced prose refs
- artifact status
- next legal actions
- whether lint/repair has not run

### Public Primitive: `lint_scene_prose`
Why public:
- The author may want diagnostics before repair.
- It produces diagnostic artifacts and can inform route selection.

### Public Primitive: `repair_scene_prose`
Why public:
- It changes provisional prose and should be reviewable.
- It may choose a repair lane later, but the lane classification is evidence, not hidden behavior.

### Public Primitive: `apply_scene_commit`
Why public:
- It changes artifact authority.
- It is a promotion-like boundary even when branch-local.

## Seam Units

### Public Primitive: `align_scene_pair`
Why public:
- It is the exact authorial operation needed to fix duplicated/altered seam content.
- The LLM rewrites two bounded windows together.
- The caller may choose it after reading a seam report or after writing a new scene.

Required scope:
- book
- branch
- chapter
- scene_a
- scene_b

Required artifacts:
- original scene A ending segment
- original scene B opening segment
- revised scene A ending segment
- revised scene B opening segment
- seam report
- receipt

Not public helpers:
- paragraph splitter
- overlap detector
- window extractor
- patch applier

### Macro Workflow: `align_chapter_seams`
Why macro:
- It composes pairwise alignment over A/B, B/C, C/D.
- The author may choose to run it, but should not be forced into it.
- It should expose child `align_scene_pair` actions and stop on refusal or approval boundary.

## Scene Insertion Units

### Public Primitive: `insert_bridge_scene`
Why public:
- It changes narrative structure.
- It can be the correct next move when a seam cannot be honestly fixed in-place.
- It requires branch-local isolation, sequence/ref-map handling, and downstream validation.

Not public helpers:
- find insertion index
- rebuild chapter markdown
- update local scene file names

## Branch Units

### Public Primitive: `create_branch`
Why public:
- It creates an isolated workspace for mutation.
- It is a safety boundary.

### Public Query: `get_branch_status`
Why public:
- Nanda branch UI and commit gate need to know branch lifecycle and staleness.

### Public Primitive: `rebase_branch`
Why public later:
- It changes branch ancestry.
- It can resolve stale-parent risk.
- It must not happen implicitly.

### Promotion Action: `promote_branch_to_main`
Why public:
- It mutates canonical state.
- It requires validation and approval.

## Recovery Units

### Public Diagnostic: `outline_lineage_audit`
Why public:
- It tells Nanda where lineage drift exists.
- It is read-only and should precede repair.

### Public Primitive: `quarantine_artifacts`
Why public:
- It changes what branch-local artifacts remain active.
- It is destructive-like and needs receipt/removal refs.

### Public Primitive: `normalize_outline_scope`
Why public:
- It chooses and materializes a timeline anchor into branch-local outline truth.

### Public Primitive: `redraft_scope`
Why public:
- It rewrites impacted prose/state in a branch.
- It should be selected after impact report and invalidation.

### Promotion Action: `promote_recovery_branch`
Why public:
- It merges recovery back to main and removes invalid canonical files.
- It requires explicit validation and approval.

## Projection Layer Units

### Public Query: `get_scene_context_projection`
Why public:
- It aggregates appearance, setting, and thought-context availability.
- It helps Nanda decide what context it can safely provide to the author.

### Public Primitive: `refresh_character_appearance_projection`
Why public:
- It refreshes a derived/provisional projection.
- It should not silently mutate canonical character truth.

### Public Primitive: `extract_scene_setting_from_prose`
Why public:
- It creates a derived setting/background projection from prose.
- Nanda must know this is derived, not authoritative.

## Reader Units

### Public Query: `get_book_reader_scene`
Why public:
- It lets Nanda display prose without filesystem archaeology.
- It declares status and source node.

### Not Public Helper: `read_markdown_file`
Why not:
- It has no narrative or workflow semantics.
- It cannot tell Nanda whether the prose is canonical, stale, quarantined, or branch-local.

## Author Asset Units

### Public Primitive: `create_author`
Why public:
- It creates a durable author asset.
- It should return versioned profile refs and receipt.

### Public Primitive: `refine_author`
Why public:
- It changes or creates a new author version.
- The author UI needs preview/approval semantics.

### Public Primitive: `select_author_version`
Why public:
- It changes active author context for a book or chat.

## Macro Recipe Examples

### `section_write_macro`
Potential child actions:
- `plan_scene`
- `preflight_scene_state`
- `generate_continuity_pack`
- `write_scene_prose`
- `state_repair_scene_patch`
- `lint_scene_prose`
- `repair_scene_prose`
- `apply_scene_commit`

Rule:
- Useful as a convenience command.
- Not the only valid path.
- The author agent may stop after any child receipt.

### `chapter_finalize_macro`
Potential child actions:
- `align_scene_pair` for each adjacent scene pair
- `run_chapter_seam_audit`
- `repair_chapter_seam_findings`
- `compile_chapter_preview`
- `validate_chapter_quality_gate`
- `promote_chapter_final`

Rule:
- Should never hide deterministic prose modifications.
- LLM-author seam alignment is separate from audit and validation.

## Bad Capability Projections

Bad:
```json
{
  "capability_id": "call_gemini",
  "unit_type": "primitive_action"
}
```

Why bad:
- Provider call is implementation detail.
- No author-level decision point.

Bad:
```json
{
  "capability_id": "write_and_repair_everything",
  "unit_type": "macro_workflow",
  "child_actions": []
}
```

Why bad:
- Hides graph traversal.
- Recreates rails.

Bad:
```json
{
  "capability_id": "book_reader",
  "mutation_class": "read_only",
  "artifact_status_outputs": ["authoritative"]
}
```

Why bad today:
- Nanda reader is currently fallback filesystem read.
- Until BookForge owns canonical reader queries, output must be diagnostic/fallback.

## Good Capability Projection Pattern

Good:
```json
{
  "capability_id": "write_scene_prose",
  "unit_type": "primitive_action",
  "action_key": "write_scene_prose",
  "supported_scope_kinds": ["scene"],
  "required_selector_shape": ["book_id", "branch_id", "chapter", "scene"],
  "branch_policy": "any",
  "mutation_class": "provisional_branch_mutation",
  "approval_required": false,
  "readiness_source": "bookforge.query.scene_phase.get_scene_phase_readiness",
  "expected_receipt_type": "execution_result_v1",
  "produced_artifact_statuses": ["provisional"],
  "refusal_semantics": {
    "missing_prerequisites": "Return readiness blockers; do not run upstream phases automatically.",
    "lineage_risk": "Refuse main-branch mutation and recommend recovery/branch path."
  }
}
```

This is useful because Nanda can decide, display, gate, dispatch, and explain the action without inventing semantics.
