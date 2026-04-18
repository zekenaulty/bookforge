# bookforge workflow

Purpose
- Run the iterative section lifecycle on top of the existing outline and writer systems.
- This is the preferred user-facing surface for the section-chunked workflow.

Core idea
- The canonical book state is never discarded.
- Only one section is exposed as the thick mutable working set at a time.
- Completed sections remain fully retained in canonical outline, registry, boundary, prose, and state artifacts, but are read-only to automatic mutation.

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

## `bookforge workflow status`

Purpose
- Show section workflow state, active section, cursor, and per-section status.

Usage
- `bookforge workflow status --book <id>`

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

## `bookforge workflow lock-section`

Purpose
- Mark a frozen section locked after scene prose/meta files exist for every scene in the section.

Usage
- `bookforge workflow lock-section --book <id> --chapter <n> --section <m>`

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
- Runs the normal writer loop only through the section's terminal scene.
- Locks the section after prose/meta validation succeeds.
- Advances the cursor to the next expected section start.

Current implementation note
- This is a transitional workflow layer.
- It links outline freeze -> write -> lock around existing batch-oriented systems.
- The lower-level batch commands still exist:
  - `bookforge outline generate`
  - `bookforge run`

Examples
- Initialize workflow state from a known outline run:
  - `bookforge --workspace workspace workflow init --book criticulous_the_rng_hellscape --run-id 20260404_041439`
- Freeze the first section:
  - `bookforge --workspace workspace workflow freeze-section --book criticulous_the_rng_hellscape --chapter 1 --section 1 --run-id 20260404_041439`
- Advance the same section end to end for controlled testing:
  - `bookforge --workspace workspace workflow advance-section --book criticulous_the_rng_hellscape --chapter 1 --section 1 --run-id 20260404_041439 --force-outline-gate-bypass`
