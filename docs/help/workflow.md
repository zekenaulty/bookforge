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
  - `state_repair_scene_patch` when scene scope is selected
  - `lint_scene_prose` when scene scope is selected
  - `repair_scene_prose` when scene scope is selected
  - `apply_scene_commit` when scene scope is selected
  - `write_frozen_section`
- Shows whether each action is allowed right now or blocked.
- Includes refusal reasons for blocked actions so operators do not have to infer transition rules from docs alone.
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
  - `state_repair_scene_patch` when the active cursor scene has a current provisional prose baseline and no current state-repair patch for that baseline
  - `lint_scene_prose` when the active cursor scene has a current state-repair patch and no current lint report for that patched baseline
  - `repair_scene_prose` when the latest current lint report fails
  - `apply_scene_commit` when the latest current lint report passes
  - `write_frozen_section` when the active frozen section still needs prose generation
- derived-branch examples:
  - `discard_branch`
  - `record_assembly_validation` for active assembly branches
  - `promote_branch_to_main` once the branch reaches `promote_ready`

## `bookforge workflow scene-readiness`

Purpose
- Show the truthful scene-phase readiness surface for one scene on the current main-branch cursor path.

Usage
- `bookforge workflow scene-readiness --book <id> --chapter <n> --scene <s> [--section <m>]`

Behavior
- Reports:
  - current scene status
  - recommended next action
  - per-action legal and ready state
  - missing prerequisites
  - available inputs
  - existing outputs with explicit artifact status
- Current first-slice scope:
  - main branch only
  - active cursor scene only
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

## `bookforge workflow plan-scene`

Purpose
- Generate a provisional scene card for one scene without auto-running downstream phases.

Usage
- `bookforge workflow plan-scene --book <id> --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`.
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
- `bookforge workflow preflight-scene-state --book <id> --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`.
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
- `bookforge workflow generate-continuity-pack --book <id> --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`.
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
- Commit one scene's latest passing provisional baseline into canonical state and authoritative scene artifacts.

Usage
- `bookforge workflow apply-scene-commit --book <id> --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`.
- Requires:
  - current scene card
  - current prose baseline (`write_prose` or newer `repair_prose`)
  - current `state_repair_patch`
  - current passing `lint_report`
- Runs the real canonical apply path for one scene:
  - applies the final state patch
  - applies character/stat updates
  - refreshes appearance projections when requested
  - applies durable mutations
  - writes authoritative scene prose/meta
  - updates bible context
  - compiles chapter outputs on chapter end
  - advances the cursor
- Emits authoritative or derived produced-artifact receipts instead of forcing callers to infer commit success from filesystem changes.
- Current implementation note:
  - this command routes through the narrow engine action `apply_scene_commit`
  - the action emits a reconciled main-branch execution result with canonical-change details

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
- `bookforge workflow write-section --book <id> --chapter <n> --section <m> [options]`

Options
- `--ack-outline-attention-items`: Pass through to the writer loop.
- `--force-outline-gate-bypass`: Pass through to the writer loop for controlled testing.

Behavior
- Requires the selected section to be the active frozen section.
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
- `bookforge workflow write-scene-prose --book <id> --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`.
- Requires the first-slice scene prerequisites to already exist:
  - `scene_card`
  - `preflight_patch`
  - `continuity_pack`
  - `style_anchor`
- Refuses truthfully when prerequisites are missing or when the live node has drifted.
- Produces provisional write artifacts only.
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
- `bookforge workflow state-repair-scene-patch --book <id> --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`.
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
- `bookforge workflow lint-scene-prose --book <id> --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`.
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
- `bookforge workflow repair-scene-prose --book <id> --chapter <n> --scene <s> [--section <m>]`

Behavior
- Requires the selected scene to be the active cursor scene on `main`.
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
- Re-runs chapter seam repair/finalization against the currently locked chapter state.
- Because the result is reconciled against current canonical state, rerunning finalization may truthfully return `no_op` when nothing changed.
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
- Main-branch workflow commands emit reconciliation details alongside result status. Derived-branch reruns and promotions are still a lower-level engine surface and are not exposed as public CLI commands yet.
- `bookforge workflow legal-actions --branch-id <id>` is the current operator-facing way to inspect derived-branch action legality without calling Python directly.
- `bookforge workflow legal-actions --fork-group-id <id>` is the current operator-facing way to inspect whether a main-branch fork group is eligible for assembly-branch creation.
- `bookforge workflow legal-actions --scene <s>` is the current operator-facing way to expose scene-scoped execution options such as `write_scene_prose`.
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
