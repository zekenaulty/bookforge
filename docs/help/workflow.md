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
- `bookforge workflow legal-actions --book <id> [--branch-id <id>] [--fork-group-id <id>] [--chapter <n>] [--section <m>]`

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
  - `resume_paused_section`
  - `write_frozen_section` when the active frozen section still needs prose generation
- derived-branch examples:
  - `discard_branch`
  - `record_assembly_validation` for active assembly branches
  - `promote_branch_to_main` once the branch reaches `promote_ready`

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
  - the CLI wrapper is no longer the only caller-visible implementation path

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
  - `write_frozen_section`
- The first legal-next-action query seam now exists below the CLI:
  - `bookforge.query.list_execution_options(...)`
  - `bookforge.query.legal_next_actions(...)`
- The lower-level commands still exist and have narrower responsibilities:
  - `bookforge outline generate` = `deep_outline`
  - `bookforge run` = `section_write`
- `bookforge workflow init`, `bookforge workflow freeze-section`, `bookforge workflow write-section`, and `bookforge workflow resume-paused-section` now run through the extracted execution layer instead of directly owning orchestration.
- `bookforge workflow lock-section` and `bookforge workflow finalize-chapter` now also run through the extracted execution layer instead of directly owning orchestration.
- `bookforge workflow advance-section` is still a macro convenience wrapper, but it now composes the extracted execution actions instead of calling its own orchestration path.
- `thin_outline` remains reserved vocabulary for a future thinner batch surface and is not a public command today.
- Main-branch workflow commands emit reconciliation details alongside result status. Derived-branch reruns and promotions are still a lower-level engine surface and are not exposed as public CLI commands yet.
- `bookforge workflow legal-actions --branch-id <id>` is the current operator-facing way to inspect derived-branch action legality without calling Python directly.
- `bookforge workflow legal-actions --fork-group-id <id>` is the current operator-facing way to inspect whether a main-branch fork group is eligible for assembly-branch creation.
- The extracted section materialization path on `main` now covers:
  - init
  - freeze
  - lock
  - finalize

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
- Inspect legal actions for a derived rerun branch:
  - `bookforge --workspace workspace workflow legal-actions --book criticulous_the_rng_hellscape --branch-id rerun-sec1 --chapter 1 --section 1`
- Inspect whether a fork group is ready for assembly-branch creation:
  - `bookforge --workspace workspace workflow legal-actions --book criticulous_the_rng_hellscape --fork-group-id fg-1 --chapter 1`
