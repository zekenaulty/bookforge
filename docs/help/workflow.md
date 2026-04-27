# bookforge workflow

Purpose
- Run the iterative section lifecycle on top of the existing outline and writer systems.
- This is the preferred user-facing surface for the section-chunked workflow.
- Runtime family: `section_local_outline` orchestrating selected `deep_outline` source artifacts plus the lower-level `section_write` loop.

Core idea
- The canonical book state is never discarded.
- Only one section is exposed as the thick mutable working set at a time.
- Completed sections remain fully retained in canonical outline, registry, boundary, prose, and state artifacts, but are read-only to automatic mutation.
- "Only one section is thick and writable" means:
  - completed sections remain fully preserved in canonical outline and prose/state artifacts
  - active mutation is limited to the currently selected section working set
  - the workflow does not reopen or rewrite the full book as one massive mutable payload

Lineage truth
- Immutable lineage anchors come from `outline/pipeline_runs/<run_id>/...` semantic handoff artifacts such as `outline_spine_v1.json`, `outline_sections_v1.json`, and `outline_final_v1_1.json`.
- Workflow files such as `outline/snapshot_registry.json`, `outline/outline.thin.json`, `outline/outline.toc.json`, `outline/outline.index.json`, `outline/outline.appendix.json`, `outline/chapters/ch_###.json`, and `outline/boundaries/*.json` are frozen projections.
- `outline/outline.json` is a mutable compatibility view. It is useful, but it is not a sufficient lineage anchor by itself when immutable run artifacts exist.
- Pointer and report files such as `outline/pipeline_latest.json` and `outline/outline_pipeline_report_latest.json` are discovery aids, not lineage truth.

Lifecycle
- `stub`: section exists only as a thin structural placeholder.
- `frozen`: section scene inventory has been promoted into canonical outline state and is ready for prose generation.
- `locked`: section prose/meta exist and the section is committed.

Commands

## `bookforge workflow init`

Purpose
- Initialize canonical workflow files from an outline pipeline run.

Usage
- `bookforge workflow init --book <id> [--run-id <run>] [--overwrite]`

Behavior
- Builds canonical `outline/outline.json` from outline spine + section artifacts.
- Creates:
  - `outline/snapshot_registry.json`
  - `outline/outline.thin.json`
  - `outline/outline.toc.json`
  - `outline/outline.index.json`
  - `outline/outline.appendix.json`
- Keeps sections as explicit stubs until they are frozen.
- Current implementation note:
  - this command now routes through the narrow engine action `initialize_section_workflow`
  - the CLI wrapper is no longer the only caller-visible implementation path

## `bookforge workflow status`

Purpose
- Show section workflow state, active section, cursor, and per-section status.

Usage
- `bookforge workflow status --book <id>`

## `bookforge workflow legal-actions`

Purpose
- Show the current narrow engine actions that are allowed or blocked for the selected scope.

Usage
- `bookforge workflow legal-actions --book <id> [--branch-id <id>] [--fork-group-id <id>] [--chapter <n>] [--section <m>] [--scene <s>]`

Behavior
- Resolves the current truth for the selected branch and scope.
- Reports the currently extracted action catalog, including:
  - `create_assembly_branch`
  - `create_branch`
  - `discard_branch`
  - `finalize_chapter_from_locked_sections`
  - `initialize_section_workflow`
  - `freeze_section_from_phase03_artifact`
  - `lock_section_from_written_state`
  - `promote_branch_to_main`
  - `record_assembly_validation`
  - `resume_paused_section`
  - `plan_scene` when scene scope is selected
  - `preflight_scene_state` when scene scope is selected
  - `generate_continuity_pack` when scene scope is selected
  - `write_scene_prose` when scene scope is selected
  - `refresh_character_appearance_projection` when scene scope is selected
  - `draft_scene_setting_projection` when scene scope is selected
  - `extract_scene_setting_from_prose` when scene scope is selected and prose exists
  - `state_repair_scene_patch` when scene scope is selected
  - `lint_scene_prose` when scene scope is selected
  - `repair_scene_prose` when scene scope is selected
  - `apply_scene_commit` when scene scope is selected
  - `create_recovery_branch` when lineage contamination exists, or when recovery scope is explicitly selected with `workflow_family=recovery_import`
  - `quarantine_artifacts` on a recovery branch
  - `normalize_outline_scope` on a recovery branch
  - `invalidate_scope_outputs` after branch-local outline normalization
  - `rebuild_state_scope` after invalidation removes generated prose/phase outputs
  - `redraft_scope` after state/projection rebuild
  - `validate_recovery_branch` after quarantine, normalization, invalidation, state rebuild, and redraft receipts exist
  - `promote_recovery_branch` after recovery branch health is clean
  - `write_frozen_section`
- Shows whether each action is allowed right now or blocked.
- Includes refusal reasons for blocked actions so operators do not have to infer transition rules from docs alone.
- If outline lineage audit reports `chimera_risk`, unsafe main-branch mutation actions are blocked with affected scope details. Use `outline-lineage-audit` and `section-lineage-matrix` before repair.
- `main` branch examples:
  - `create_assembly_branch` when fork-group scope resolves to sibling branches that can be assembled
  - `finalize_chapter_from_locked_sections` when a chapter's sections are already locked
  - `initialize_section_workflow`
  - `create_branch`
  - `freeze_section_from_phase03_artifact`
  - `lock_section_from_written_state` when a frozen section has complete prose/meta artifacts
  - `plan_scene` when the active cursor scene has no scene card yet and the active frozen section is valid
  - `preflight_scene_state` when the active cursor scene has a scene card but no preflight patch
  - `generate_continuity_pack` when the active cursor scene has scene-card and preflight artifacts but no continuity pack
  - `resume_paused_section`
  - `write_scene_prose` when the active cursor scene has the required scene-card, preflight, continuity, and style-anchor inputs
  - `refresh_character_appearance_projection` when a scene scope has a current execution node and the caller wants a derived, non-mutating appearance projection for the scene/cast
  - `draft_scene_setting_projection` when a scene scope has a current execution node and the caller wants to record provisional author setting intent
  - `extract_scene_setting_from_prose` when a scene scope has existing prose and the caller wants to record derived setting observations from that prose
  - `state_repair_scene_patch` when the active cursor scene has a current provisional prose baseline and no current state-repair patch for that baseline
  - `lint_scene_prose` when the active cursor scene has a current state-repair patch and no current lint report for that patched baseline
  - `repair_scene_prose` when the latest current lint report fails
  - `apply_scene_commit` when the latest current lint report passes
  - `write_frozen_section` when the active frozen section still needs prose generation
- derived-branch examples:
  - `discard_branch`
  - `record_assembly_validation` for active assembly branches
  - `promote_branch_to_main` once the branch reaches `promote_ready`
  - `quarantine_artifacts`, `normalize_outline_scope`, `invalidate_scope_outputs`, `rebuild_state_scope`, `redraft_scope`, `validate_recovery_branch`, and `promote_recovery_branch` for branches created with recovery manifests

## Outline Lineage Audit Commands

Purpose
- Diagnose outline-pass bleed, stale section drafts, and mixed-lineage materialization before the author system mutates a book.
- These commands are read-only. They do not repair, quarantine, restore, rewrite, or promote anything.

Commands
- `bookforge workflow outline-lineage-audit --book <id> [--branch-id <id>] [--json]`
- `bookforge workflow section-lineage-matrix --book <id> [--branch-id <id>] [--chapter <n>] [--section <m>] [--json]`
- `bookforge workflow stale-outline-artifacts --book <id> [--branch-id <id>] [--json]`
- `bookforge workflow outline-repair-candidates --book <id> [--branch-id <id>] [--json]`

Behavior
- `outline-lineage-audit` returns the global verdict plus localized evidence:
  - declared source run
  - latest outline run
  - first technical divergence
  - first visible story divergence when detectable from structured artifact casts
  - affected section count
  - repair candidates
- `section-lineage-matrix` compares section scopes across:
  - declared immutable source run
  - latest outline run
  - frozen chapter projection
  - mutable `outline.json`
  - section draft artifact
- Matrix rows include normalized section/scene hashes, differing fields, scene count deltas, character cohort deltas, artifact mtimes, suspected contamination class, and recommended safe next action.
- `stale-outline-artifacts` lists section drafts, mutable compatibility views, and outline projections with artifact class/status and whether each is safe to consume as canonical.
- `outline-repair-candidates` returns non-mutating recovery options such as:
  - `inspect_only`
  - `choose_recovery_anchor`
  - `create_recovery_branch_from_selected_lineage`
  - `restore_affected_sections_from_declared_source_run`
  - `restore_affected_sections_from_frozen_chapter_projection`
  - `quarantine_stale_section_drafts`
  - `shelf_book`
- Mutation-capable recovery actions are now available, but only through explicit recovery branches with receipts and validation gates.
- Nanda should use these surfaces before answering content questions about contaminated books or before presenting author repair choices.

## Timeline Recovery Commands

Purpose
- Execute author-approved timeline recovery or story-weaving plans through branch-first primitives.
- These commands are composable tools, not a bespoke fixer for one book.
- The author/Nanda side should still produce an impact report and choose the recovery anchor before mutation.

Commands
- `bookforge workflow create-recovery-branch --book <id> --anchor-type <type> [--source-run-id <run>] [--branch-id <id>] [--affected-scope <scope>] [--salvage-policy <policy>]`
- `bookforge workflow recovery-readiness --book <id> --branch-id <id> [--impact-report-ref <ref>] [--json]`
- `bookforge workflow recovery-health --book <id> --branch-id <id> [--json]`
- `bookforge workflow recovery-blast-radius --book <id> --branch-id <id> [--json]`
- `bookforge workflow scope-invalidation-preview --book <id> --branch-id <id> [--json]`
- `bookforge workflow state-rebuild-preview --book <id> --branch-id <id> [--json]`
- `bookforge workflow quarantine-artifacts --book <id> --branch-id <id>`
- `bookforge workflow normalize-outline-scope --book <id> --branch-id <id>`
- `bookforge workflow invalidate-scope-outputs --book <id> --branch-id <id>`
- `bookforge workflow rebuild-state-scope --book <id> --branch-id <id>`
- `bookforge workflow redraft-scope --book <id> --branch-id <id>`
- `bookforge workflow validate-recovery-branch --book <id> --branch-id <id>`
- `bookforge workflow promote-recovery-branch --book <id> --branch-id <id>`

Anchor types
- `declared_source_run`: rebuild affected scopes from the source run declared by workflow lineage.
- `latest_outline_run`: rebuild from the selected/latest outline run.
- `frozen_chapter_projection`: rebuild from branch-local frozen chapter projection files.
- `manual_hybrid`: reserved for future human-approved hybrid recovery.
- `shelf`: reserved for explicit no-repair/shelf decisions.

Scope syntax
- `--affected-scope 1` means chapter 1.
- `--affected-scope 1:2` means chapter 1, section 2.
- `--affected-scope 1:2:3` means chapter 1, section 2, scene 3.
- Repeat `--affected-scope` for multiple scopes.
- If omitted, `create-recovery-branch` defaults to affected sections from `outline-lineage-audit`.

Recovery sequence
- `create-recovery-branch` derives an isolated branch with workflow family `recovery_import`.
- The recovery branch copies the outline evidence normal rerun branches omit:
  - `outline/pipeline_runs`
  - `outline/section_drafts`
  - latest outline pointer/report files when present
- `quarantine-artifacts` moves stale section-draft artifacts out of the active branch snapshot and records promotion removals.
- `normalize-outline-scope` replaces affected branch outline scopes from the selected anchor and rebuilds branch-local outline projections.
- `scope-invalidation-preview` shows which branch-local prose/generated outputs would be quarantined.
- `invalidate-scope-outputs` quarantines affected prose/generated outputs and records promotion removals.
- `state-rebuild-preview` shows which branch-local state, continuity, durable-state, phase-history, appearance, and setting projection artifacts would be quarantined.
- `recovery-blast-radius` combines prose invalidation and state rebuild previews into impact families:
  - prose
  - state
  - continuity
  - projection
  - series
- The series family is diagnostic-only in this slice. It lets Nanda include series canon risk in an impact report without pretending BookForge can mutate series canon through recovery promotion yet.
- `rebuild-state-scope` quarantines those branch-local state/projection artifacts, records promotion removals, and writes a clean outline-derived state baseline.
- `redraft-scope` marks normalized affected sections as branch-local frozen sections and invokes the existing scoped section writer inside the recovery branch.
- `validate-recovery-branch` refuses promotion while branch-local lineage still reports `chimera_risk` or required receipts are missing.
- `promote-recovery-branch` promotes only a healthy branch and applies recorded removals before copying branch snapshot data to `main`.
- `promote-recovery-branch` returns a canonical postcondition with pre/post outline-lineage status, pre/post integrity status, planned/applied removals, and whether `main` cleared chimera risk.

Truth rules
- Recovery mutation never writes directly to contaminated `main`.
- Every branch-local recovery receipt includes a postcondition snapshot with branch health, outline lineage status, completed/remaining required receipts, blockers/warnings, approval metadata, and the recommended next recovery action.
- Receipt prerequisites are status-aware: a failed validation attempt does not count as a completed validation receipt.
- Existing polluted prose is salvage/reference material only unless later redrafted or explicitly promoted by a future tool.
- `rebuild-state-scope` currently performs a conservative full-book context reset inside the recovery branch because state history is not yet event-sourced enough for safe partial rollback.
- `redraft-scope` may invoke LLM-backed writing. It should be run with the same long timeout expectations as normal section writing.
- A recovery branch can become timeline-healthy while still needing author revision, prose redraft, seam repair, or downstream story weaving.

## Branch Lifecycle Commands

Purpose
- Provide operator-facing access to the branch lifecycle primitives used by Nanda and the engine action surface.

Commands
- `bookforge workflow create-branch --book <id> [--branch-id <id>] [--parent-branch-id <id>] [--fork-group-id <id>] [--chapter <n>] [--section <m>] [--branch-role <role>] [--merge-operation <op>]`
- `bookforge workflow create-assembly-branch --book <id> --fork-group-id <id> [--chapter <n>] [--branch-id <id>]`
- `bookforge workflow discard-branch --book <id> --branch-id <id> [--reason <text>]`
- `bookforge workflow promote-branch --book <id> --branch-id <id> [--target-branch-id <id>]`
- `bookforge workflow rebase-branch --book <id> --branch-id <id> [--new-branch-id <id>]`
- `bookforge workflow validate-assembly-branch --book <id> --branch-id <id>`
- `bookforge workflow record-assembly-validation --book <id> --branch-id <id> (--passed | --failed) [--message <text>]`

Behavior
- `create-branch` derives a branch from `main` by default, or from `--parent-branch-id` when a nested branch is needed.
- `promote-branch` promotes to `main` by default, or into `--target-branch-id` for parent-target promotion.
- `rebase-branch` is conservative: it creates a refreshed child branch from the current parent snapshot and discards the old branch without erasing its history.
- `create-assembly-branch` creates an off-parent assembly branch for a fork group; it does not promote assembled content by itself.
- When sibling branches contain scoped writer outputs, `create-assembly-branch` stages those draft scene files into the assembly branch snapshot for validation.
- `validate-assembly-branch` deterministically checks that expected scoped sibling writer files are present in the assembly snapshot and records pass/fail.
- `record-assembly-validation` records whether the assembly branch has passed validation before promotion.
- These commands emit execution receipts with node, branch, status, and details instead of requiring raw branch manifest inspection.

## `bookforge workflow scene-readiness`

Purpose
- Show the truthful scene-phase readiness surface for one scene on `main` or a selected derived branch.

Usage
- `bookforge workflow scene-readiness --book <id> [--branch-id <id>] --chapter <n> --scene <s> [--section <m>]`

Behavior
- Reports:
  - current scene status
  - recommended next action
  - per-action legal and ready state
  - missing prerequisites
  - available inputs
  - existing outputs with explicit artifact status
- Branch scope:
  - `main` still requires the selected scene to match the active cursor scene.
  - derived branches resolve against the branch-local current node, active section, and snapshot root.
  - unknown, discarded, or promoted branches return truthful refusal details instead of falling back to `main`.
  - copied committed scene files inside a derived branch are treated as replaceable branch baselines, not canonical overwrite permission.
- phase rows currently exposed:
  - `plan_scene`
  - `preflight_scene_state`
  - `generate_continuity_pack`
  - `write_scene_prose`
  - `state_repair_scene_patch`
  - `lint_scene_prose`
  - `repair_scene_prose`
  - `apply_scene_commit`
- This slice now has matching executable actions for:
  - `plan_scene`
  - `preflight_scene_state`
  - `generate_continuity_pack`
  - `write_scene_prose`
  - `state_repair_scene_patch`
  - `lint_scene_prose`
  - `repair_scene_prose`
  - `apply_scene_commit`
- This is the truthful query surface behind deeper author control.
- It exists so callers do not have to infer scene readiness from file presence or persona text.

## Projection Query Surfaces

Purpose
- Expose scene-context projections that Nanda can query without reading prompt logs or treating prose as hidden state.

Python surfaces
- `bookforge.query.list_appearance_projection_views(...)`
- `bookforge.query.get_scene_setting_projection(...)`
- `bookforge.query.get_scene_context_projection(...)`
- `bookforge.query.get_thought_context_projection(...)`
- `bookforge.execution.build_refresh_character_appearance_projection_request(...)`
- `bookforge.execution.refresh_character_appearance_projection(...)`
- `bookforge.execution.build_draft_scene_setting_projection_request(...)`
- `bookforge.execution.draft_scene_setting_projection(...)`
- `bookforge.execution.build_extract_scene_setting_from_prose_request(...)`
- `bookforge.execution.extract_scene_setting_from_prose(...)`

Behavior
- Appearance projections are book-rooted and can narrow by branch, chapter, section, scene, and character.
- `get_scene_context_projection` aggregates appearance, setting, and prior T1 thought-context availability for a scene without making callers stitch raw files together.
- Existing character appearance is labeled truthfully as `derived`, `provisional`, or `diagnostic` unless a stronger artifact status is explicitly present.
- Scene setting projections distinguish:
  - `author_drafted` as `provisional`
  - `prose_extracted` as `derived`
  - `outline_derived` as `derived`
  - missing setting as `diagnostic`
- Prior T1 thought signatures are exposed as diagnostic planning-reuse context only.
- Thought signatures are never treated as proof of execution truth; execution receipts remain authoritative for what happened.
- `refresh_character_appearance_projection` writes a derived projection artifact for the selected scene/cast and records a produced-artifact receipt without mutating character truth.
- `draft_scene_setting_projection` writes a provisional author-drafted setting artifact and records a produced-artifact receipt without mutating scene or location truth.
- `extract_scene_setting_from_prose` writes a derived prose-extracted setting artifact and refuses when no scene prose exists.

## `bookforge workflow plan-scene`

Purpose
- Generate a provisional scene card for one scene without auto-running downstream phases.

Usage
- `bookforge workflow plan-scene --book <id> [--branch-id <id>] --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`, or the branch-local active scene when `--branch-id` targets a derived branch.
- Produces only the provisional scene-card artifact for the current scene.
- Does not auto-run:
  - preflight
  - continuity generation
  - prose generation
  - lint
  - repair
  - commit
- Current implementation note:
  - this command routes through the narrow engine action `plan_scene`
  - the action records a typed produced-artifact receipt for the generated scene card

## `bookforge workflow preflight-scene-state`

Purpose
- Generate a provisional preflight state patch for one scene without applying it.

Usage
- `bookforge workflow preflight-scene-state --book <id> [--branch-id <id>] --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`, or the branch-local active scene when `--branch-id` targets a derived branch.
- Requires an existing provisional scene card.
- Produces only the provisional preflight patch artifact for the current scene.
- Does not apply the patch to:
  - `state.json`
  - character state files
  - durable inventory/state layers
- Does not auto-run:
  - continuity generation
  - prose generation
  - lint
  - repair
  - commit
- Current implementation note:
  - this command routes through the narrow engine action `preflight_scene_state`
  - the action records a typed produced-artifact receipt for the generated preflight patch

## `bookforge workflow generate-continuity-pack`

Purpose
- Generate a derived continuity pack for one scene without writing prose or mutating canonical state.

Usage
- `bookforge workflow generate-continuity-pack --book <id> [--branch-id <id>] --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`, or the branch-local active scene when `--branch-id` targets a derived branch.
- Requires an existing provisional scene card and provisional preflight state patch.
- Produces only the derived continuity-pack artifact for the current scene.
- Applies safe preflight patch materialization only to an in-memory working state.
- Refuses when the preflight patch contains provisional character, continuity-system, or durable mutations this slice cannot truthfully materialize yet.
- Does not mutate:
  - `state.json`
  - character state files
  - durable inventory/state layers
- Does not auto-run:
  - prose generation
  - lint
  - repair
  - commit
- Current implementation note:
  - this command routes through the narrow engine action `generate_continuity_pack`
  - the action records a typed produced-artifact receipt with artifact status `derived`

## `bookforge workflow apply-scene-commit`

Purpose
- Commit one scene's latest passing provisional baseline into the selected execution root.

Usage
- `bookforge workflow apply-scene-commit --book <id> [--branch-id <id>] --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`, or the branch-local active scene when `--branch-id` targets a derived branch.
- Requires:
  - current scene card
  - current prose baseline (`write_prose` or newer `repair_prose`)
  - current `state_repair_patch`
  - current passing `lint_report`
- Runs the real apply path for one scene:
  - applies the final state patch
  - applies character/stat updates
  - refreshes appearance projections when requested
  - applies durable mutations
  - writes authoritative scene prose/meta in the selected execution root
  - updates bible context
  - compiles chapter outputs on chapter end
  - advances the cursor
- Emits authoritative or derived produced-artifact receipts instead of forcing callers to infer commit success from filesystem changes.
- On `main`, existing committed scene files are protected and block accidental overwrite.
- In a derived branch, existing copied scene files are replaceable branch-local baselines; replacement preserves `.original` backups before writing the new branch-local authoritative scene files.
- Current implementation note:
  - this command routes through the narrow engine action `apply_scene_commit`
  - the action emits a reconciled main-branch result on `main` or a branch-local reconciled result when `--branch-id` is selected

## `bookforge workflow freeze-section`

Purpose
- Promote one section into canonical outline state from an existing phase-03 chapter artifact.

Usage
- `bookforge workflow freeze-section --book <id> --chapter <n> --section <m> [--run-id <run>]`

Behavior
- Copies only the selected section's scene inventory into `outline/outline.json`.
- Emits `outline/boundaries/ch_<NNN>_sec_<MMM>_boundary.json`.
- Marks the section `frozen` in `outline/snapshot_registry.json`.
- Leaves all other sections as stubs unless they were already frozen/locked.
- Current implementation note:
  - this command now routes through the narrow engine action `freeze_section_from_phase03_artifact`
  - the CLI wrapper is no longer the only caller-visible implementation path

## `bookforge workflow lock-section`

Purpose
- Mark a frozen section locked after scene prose/meta files exist for every scene in the section.

Usage
- `bookforge workflow lock-section --book <id> --chapter <n> --section <m>`

Behavior
- Validates that all required scene prose/meta files exist for the selected frozen section.
- Commits the section as `locked` in canonical workflow state.
- May also trigger chapter seam finalization when the chapter becomes fully locked.
- Current implementation note:
  - this command now routes through the narrow engine action `lock_section_from_written_state`
  - the CLI wrapper is no longer the only caller-visible implementation path

## `bookforge workflow write-section`

Purpose
- Run the `section_write` loop for the active frozen section through its terminal scene without locking it.

Usage
- `bookforge workflow write-section --book <id> [--branch-id <id>] --chapter <n> --section <m> [options]`

Options
- `--ack-outline-attention-items`: Pass through to the writer loop.
- `--force-outline-gate-bypass`: Pass through to the writer loop for controlled testing.

Behavior
- Requires the selected section to be the active frozen section.
- `main` writes against canonical book state.
- `--branch-id <id>` writes against that branch's snapshot root, branch-local current node, and branch-local active section.
- Refuses if a pause marker is already present; paused execution must use `resume-paused-section`.
- Writes only through the section's terminal scene.
- Leaves locking as a separate explicit action.
- May truthfully return `no_op` if all required scene prose/meta artifacts already exist.
- Current implementation note:
  - this command routes through the narrow engine action `write_frozen_section`
  - the action now reaches scene output through a dedicated section-range executor that traverses the same extracted scene-phase sequence used by `bookforge run`
  - the CLI wrapper is no longer the only caller-visible implementation path

## `bookforge workflow write-scene-prose`

Purpose
- Generate provisional prose for one scene without auto-running lint, repair, or commit.

Usage
- `bookforge workflow write-scene-prose --book <id> [--branch-id <id>] --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`, or the branch-local active scene when `--branch-id` targets a derived branch.
- Requires the first-slice scene prerequisites to already exist:
  - `scene_card`
  - `preflight_patch`
  - `continuity_pack`
  - `style_anchor`
- Refuses truthfully when prerequisites are missing or when the live node has drifted.
- Produces provisional write artifacts only.
- In a derived branch, copied committed scene prose is a replaceable baseline and does not by itself block a new provisional prose pass.
- Does not auto-run:
  - lint
  - repair
  - state repair
  - commit
- Current implementation note:
  - this command routes through the narrow engine action `write_scene_prose`
  - the action emits explicit produced-artifact receipts so callers can inspect artifact truth without reverse-engineering phase-history files

## `bookforge workflow state-repair-scene-patch`

Purpose
- Generate a provisional corrected state patch for one scene without linting, repairing prose, or committing.

Usage
- `bookforge workflow state-repair-scene-patch --book <id> [--branch-id <id>] --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`, or the branch-local active scene when `--branch-id` targets a derived branch.
- Requires existing first-slice scene artifacts:
  - `scene_card`
  - `preflight_patch`
  - `continuity_pack`
  - the current provisional prose artifact pair:
    - `write_prose` + `write_patch`
    - or `repair_prose` + `repair_patch` after a newer repair pass
- Produces only the provisional state-repair patch artifact for the current scene.
- Applies safe preflight patch materialization only to an in-memory working state.
- Refuses when the preflight patch contains provisional character, continuity-system, or durable mutations this slice cannot truthfully materialize yet.
- Does not mutate:
  - `state.json`
  - character state files
  - durable inventory/state layers
- Does not auto-run:
  - lint
  - repair
  - commit
- Current implementation note:
  - this command routes through the narrow engine action `state_repair_scene_patch`
  - the action records a typed produced-artifact receipt with artifact status `provisional`

## `bookforge workflow lint-scene-prose`

Purpose
- Generate a provisional lint report for one scene without repairing prose or committing.

Usage
- `bookforge workflow lint-scene-prose --book <id> [--branch-id <id>] --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`, or the branch-local active scene when `--branch-id` targets a derived branch.
- Requires existing first-slice scene artifacts:
  - `scene_card`
  - `preflight_patch`
  - `continuity_pack`
  - the current provisional prose artifact:
    - `write_prose`
    - or `repair_prose` after a newer repair pass
  - the current `state_repair_patch` for that prose baseline
- Produces only the provisional lint report artifact for the current scene.
- Applies safe preflight and state-repair patch materialization only to in-memory working states.
- Refuses when the preflight patch contains provisional character, continuity-system, or durable mutations this slice cannot truthfully materialize yet.
- Does not auto-run:
  - prose repair
  - state repair
  - commit
- Current implementation note:
  - this command routes through the narrow engine action `lint_scene_prose`
  - the action records a typed produced-artifact receipt with artifact status `provisional`
  - when lint passes, the truthful next extracted action is now `apply_scene_commit`

## `bookforge workflow repair-scene-prose`

Purpose
- Generate provisional repaired prose and repair-patch artifacts for one scene without rerunning state repair, lint, or commit.

Usage
- `bookforge workflow repair-scene-prose --book <id> [--branch-id <id>] --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`, or the branch-local active scene when `--branch-id` targets a derived branch.
- Requires:
  - `scene_card`
  - the current provisional prose artifact:
    - `write_prose`
    - or `repair_prose` if a prior repair is already the current baseline
  - the latest current `lint_report`, and that report must fail
- Produces only:
  - `repair_prose`
  - `repair_patch`
- Does not auto-run:
  - state repair
  - lint
  - commit
- Current implementation note:
  - this command routes through the narrow engine action `repair_scene_prose`
  - after it runs, the readiness surface should reopen `state_repair_scene_patch` against the repaired prose baseline

## `bookforge workflow finalize-chapter`

Purpose
- Run pairwise seam repair and chapter finalization for a chapter whose sections are already locked.

Usage
- `bookforge workflow finalize-chapter --book <id> --chapter <n>`

Behavior
- Runs chapter seam repair/finalization against the currently locked chapter state when the chapter is not already finalized.
- Returns `no_op` when the chapter is already finalized and has a recorded final markdown artifact.
- Current implementation note:
  - this command now routes through the narrow engine action `finalize_chapter_from_locked_sections`
  - the CLI wrapper is no longer the only caller-visible implementation path

## `bookforge workflow advance-section`

Purpose
- Freeze, write, and lock a section end to end.

Usage
- `bookforge workflow advance-section --book <id> --chapter <n> --section <m> [options]`

Options
- `--run-id`: Optional source outline pipeline run id.
- `--resume`: Resume the underlying writer loop.
- `--ack-outline-attention-items`: Pass through to the writer loop.
- `--force-outline-gate-bypass`: Pass through to the writer loop for controlled testing.

Behavior
- Freezes the selected section into canonical outline state.
- Runs either `write_frozen_section` or `resume_paused_section` depending on whether `--resume` is set.
- Locks the section after the extracted write action exits cleanly and prose/meta validation succeeds.
- Advances the cursor to the next expected section start.
- Current implementation note:
  - this remains a macro convenience wrapper
  - the write portion now routes through the dedicated section-range executor rather than calling the generic batch `run` entry point directly

## `bookforge workflow resume-paused-section`

Purpose
- Resume the currently paused `section_write` node on `main` through a truthful narrow execution path.

Usage
- `bookforge workflow resume-paused-section --book <id> [--chapter <n>] [--section <m>] [options]`

Options
- `--chapter`: Optional expected active chapter id.
- `--section`: Optional expected active section id.
- `--ack-outline-attention-items`: Pass through to the writer loop.
- `--force-outline-gate-bypass`: Pass through to the writer loop for controlled testing.

Behavior
- Resolves the current paused main-branch node.
- Refuses if the live node does not match the expected node, branch, workflow family, or active section scope.
- Resumes only the active frozen section to its terminal scene.
- Locks the section if the resumed writer loop exits cleanly.
- Current implementation note:
  - the resumed write path now flows through the dedicated section-range executor over the extracted scene-phase sequence
  - resume no longer depends on a separate monolithic per-scene implementation or on direct reuse of the generic batch `run` entry point
- Returns a truthful pause/fail result instead of silently switching into a different mode.
- Emitted execution results now include reconciliation fields so callers can tell:
  - whether the command changed canonical main-branch state
  - whether integrity improved, worsened, or stayed unchanged
  - which revision was observed before and after execution

Current implementation note
- This is a transitional workflow layer.
- It links outline freeze -> write -> lock around existing batch-oriented systems.
- The first extracted narrow action surface now exists below the CLI:
  - `create_branch` (programmatic action surface only for now)
  - `discard_branch` (programmatic action surface only for now)
  - `finalize_chapter_from_locked_sections`
  - `initialize_section_workflow`
  - `freeze_section_from_phase03_artifact`
  - `lock_section_from_written_state`
  - `promote_branch_to_main` (programmatic action surface only for now)
  - `record_assembly_validation` (programmatic action surface only for now)
  - `resume_paused_section`
  - `generate_continuity_pack`
  - `state_repair_scene_patch`
  - `lint_scene_prose`
  - `repair_scene_prose`
  - `write_frozen_section`
- The first legal-next-action query seam now exists below the CLI:
  - `bookforge.query.list_execution_options(...)`
  - `bookforge.query.legal_next_actions(...)`
- The first scene-phase readiness seam now exists below the CLI:
  - `bookforge.query.get_scene_phase_readiness(...)`
- The lower-level commands still exist and have narrower responsibilities:
  - `bookforge outline generate` = `deep_outline`
  - `bookforge run` = `section_write`
- `bookforge workflow init`, `bookforge workflow freeze-section`, `bookforge workflow write-section`, and `bookforge workflow resume-paused-section` now run through the extracted execution layer instead of directly owning orchestration.
- `bookforge workflow lock-section` and `bookforge workflow finalize-chapter` now also run through the extracted execution layer instead of directly owning orchestration.
- `bookforge workflow write-section`, `bookforge workflow resume-paused-section`, and `bookforge workflow advance-section` now use a dedicated section-range macro over the extracted scene-phase actions rather than calling the generic batch `run` surface directly.
- `bookforge workflow advance-section` is still a macro convenience wrapper, but it now composes the extracted execution actions instead of calling its own orchestration path.
- `thin_outline` remains reserved vocabulary for a future thinner batch surface and is not a public command today.
- Main-branch workflow commands emit reconciliation details alongside result status.
- Scene-phase commands and `write-section` now accept `--branch-id <id>` for derived-branch execution roots.
- Derived-branch lifecycle operations such as create/discard/promote/rebase are still a lower-level engine surface and are not exposed as public CLI commands yet.
- `bookforge workflow legal-actions --branch-id <id>` is the current operator-facing way to inspect derived-branch action legality without calling Python directly.
- `bookforge workflow legal-actions --fork-group-id <id>` is the current operator-facing way to inspect whether a main-branch fork group is eligible for assembly-branch creation.
- `bookforge workflow legal-actions --scene <s>` is the current operator-facing way to expose scene-scoped execution options such as `write_scene_prose`.
- `bookforge workflow scene-readiness --branch-id <id>` is the operator-facing way to inspect branch-local scene-phase readiness without reading branch files directly.
- `bookforge workflow create-branch`, `promote-branch`, `rebase-branch`, `discard-branch`, `create-assembly-branch`, `validate-assembly-branch`, and `record-assembly-validation` expose the first operator-facing branch lifecycle controls.
- The extracted section materialization path on `main` now covers:
  - init
  - freeze
  - lock
  - finalize
- The first extracted scene-phase path on `main` now covers:
  - readiness query
  - scene planning without implicit downstream phase execution
  - preflight state-patch generation without applying the patch
  - continuity-pack generation without implicit prose/lint/repair/commit
  - pure prose generation without implicit lint/repair/commit
  - state-repair patch generation without implicit lint/repair/commit
  - lint-report generation without implicit repair/commit
  - prose-repair generation without implicit state-repair/lint/commit

Examples
- Initialize workflow state from a known outline run:
  - `bookforge --workspace workspace workflow init --book criticulous_the_rng_hellscape --run-id 20260404_041439`
- Freeze the first section:
  - `bookforge --workspace workspace workflow freeze-section --book criticulous_the_rng_hellscape --chapter 1 --section 1 --run-id 20260404_041439`
- Write the active frozen section without locking it yet:
  - `bookforge --workspace workspace workflow write-section --book criticulous_the_rng_hellscape --chapter 1 --section 1 --ack-outline-attention-items`
- Lock the first section after prose/meta artifacts exist:
  - `bookforge --workspace workspace workflow lock-section --book criticulous_the_rng_hellscape --chapter 1 --section 1`
- Re-run chapter seam finalization on a locked chapter:
  - `bookforge --workspace workspace workflow finalize-chapter --book criticulous_the_rng_hellscape --chapter 1`
- Advance the same section end to end for controlled testing:
  - `bookforge --workspace workspace workflow advance-section --book criticulous_the_rng_hellscape --chapter 1 --section 1 --run-id 20260404_041439 --force-outline-gate-bypass`
- Resume the exact paused section without silently changing scope:
  - `bookforge --workspace workspace workflow resume-paused-section --book criticulous_the_rng_hellscape --chapter 1 --section 1`
- Inspect which narrow engine actions are currently legal:
  - `bookforge --workspace workspace workflow legal-actions --book criticulous_the_rng_hellscape --chapter 1 --section 1`
- Inspect scene-phase readiness for the active cursor scene:
  - `bookforge --workspace workspace workflow scene-readiness --book criticulous_the_rng_hellscape --chapter 1 --scene 1 --section 1`
- Generate a provisional scene card for the active cursor scene only:
  - `bookforge --workspace workspace workflow plan-scene --book criticulous_the_rng_hellscape --chapter 1 --scene 1 --section 1`
- Generate a provisional preflight state patch for the active cursor scene only:
  - `bookforge --workspace workspace workflow preflight-scene-state --book criticulous_the_rng_hellscape --chapter 1 --scene 1 --section 1`
- Generate a derived continuity pack for the active cursor scene only:
  - `bookforge --workspace workspace workflow generate-continuity-pack --book criticulous_the_rng_hellscape --chapter 1 --scene 1 --section 1`
- Generate provisional prose for the active cursor scene only:
  - `bookforge --workspace workspace workflow write-scene-prose --book criticulous_the_rng_hellscape --chapter 1 --scene 1 --section 1`
- Inspect scene-phase readiness inside a derived branch:
  - `bookforge --workspace workspace workflow scene-readiness --book criticulous_the_rng_hellscape --branch-id rewrite-ch1-sc1 --chapter 1 --scene 1 --section 1`
- Create a scene rewrite branch from `main`:
  - `bookforge --workspace workspace workflow create-branch --book criticulous_the_rng_hellscape --branch-id rewrite-ch1-sc1 --chapter 1 --section 1 --branch-role scene`
- Create a nested scene branch from a chapter branch:
  - `bookforge --workspace workspace workflow create-branch --book criticulous_the_rng_hellscape --parent-branch-id chapter-1-rewrite --branch-id rewrite-ch1-sc1 --chapter 1 --section 1 --branch-role scene`
- Generate provisional prose inside a derived branch without touching `main`:
  - `bookforge --workspace workspace workflow write-scene-prose --book criticulous_the_rng_hellscape --branch-id rewrite-ch1-sc1 --chapter 1 --scene 1 --section 1`
- Commit a rewritten scene inside a derived branch while preserving the branch snapshot's original scene as `.original` backup:
  - `bookforge --workspace workspace workflow apply-scene-commit --book criticulous_the_rng_hellscape --branch-id rewrite-ch1-sc1 --chapter 1 --scene 1 --section 1`
- Promote a scene branch back into its parent branch:
  - `bookforge --workspace workspace workflow promote-branch --book criticulous_the_rng_hellscape --branch-id rewrite-ch1-sc1 --target-branch-id chapter-1-rewrite`
- Rebase a stale branch into a refreshed child:
  - `bookforge --workspace workspace workflow rebase-branch --book criticulous_the_rng_hellscape --branch-id rewrite-ch1-sc1 --new-branch-id rewrite-ch1-sc1-rebased`
- Validate an assembly branch after staging sibling writer outputs:
  - `bookforge --workspace workspace workflow validate-assembly-branch --book criticulous_the_rng_hellscape --branch-id assembly-ch1`
- Generate a provisional corrected state patch for the active cursor scene only:
  - `bookforge --workspace workspace workflow state-repair-scene-patch --book criticulous_the_rng_hellscape --chapter 1 --scene 1 --section 1`
- Generate a provisional lint report for the active cursor scene only:
  - `bookforge --workspace workspace workflow lint-scene-prose --book criticulous_the_rng_hellscape --chapter 1 --scene 1 --section 1`
- Generate provisional repaired prose for the active cursor scene only after a failing lint report:
  - `bookforge --workspace workspace workflow repair-scene-prose --book criticulous_the_rng_hellscape --chapter 1 --scene 1 --section 1`
- Inspect legal actions for a derived rerun branch:
  - `bookforge --workspace workspace workflow legal-actions --book criticulous_the_rng_hellscape --branch-id rerun-sec1 --chapter 1 --section 1`
- Inspect whether a fork group is ready for assembly-branch creation:
  - `bookforge --workspace workspace workflow legal-actions --book criticulous_the_rng_hellscape --fork-group-id fg-1 --chapter 1`
