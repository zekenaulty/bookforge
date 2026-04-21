# BookForge Planning Guide

## Purpose
This is the planning system for BookForge.

Goals:
- keep active plans easy to scan
- isolate scope by folder instead of long file names
- make plan artifacts usable by humans and agents
- keep planning, execution, and historical reference clearly separated
- stop new work from drifting back into the legacy loose-file plan pile

## Core Rules
- Folder scope is the primary scope boundary.
- Every new active plan lives in its own plan folder.
- Do not create new loose in-flight plan files at the root of `resources/plans/`.
- Use concise semantic names. Let the path carry most of the scope.
- Keep planning records separate from implementation artifacts and runtime logs.
- `_Pinned/` is legacy and reference-only for planning purposes unless a migration step explicitly says otherwise.

## Current Local Shape
This repo is mid-migration.

Current planning roots:
- `resources/plans/Drafts`
- `resources/plans/_Pinned`
- `resources/plans/compile-plan.py`
- `resources/plans/readme.md`

Meaning:
- `Drafts/` is the source-of-truth home for new folderized plans.
- `_Pinned/` holds older loose-file plans, historical material, and reference planning context that still matters during migration.
- New active planning work should not be started inside `_Pinned/`.

## Target Stage Model
BookForge should converge toward the same folderized stage model used in Nanda.

Target roots:
- `resources/plans/Brainstorms`
- `resources/plans/Drafts`
- `resources/plans/InProgress`
- `resources/plans/Completed`
- `resources/plans/Archived/Brainstorms`
- `resources/plans/Archived/Drafts`
- `resources/plans/Archived/CompletedHistory`
- `resources/plans/Templates`

Default flow:
1. `Brainstorms`
2. `Drafts`
3. `InProgress`
4. `Completed`

Until that normalization is complete, treat `Drafts/` as the active stage root and `_Pinned/` as legacy reference.

## Plan Folder Rules
Each new active plan folder should contain:
- `plan.md`
- `steps/`
- `artifacts/`
- `validation/`
- `decisions/`
- `risks/`

Optional:
- `notes/`
- `archive-note.md`

Example:

```text
resources/plans/Drafts/bookforge-supervisable-engine/
  plan.md
  steps/
    index.md
    0010-freeze-scope-lineage-and-contract-vocabulary/
      step.md
  artifacts/
  validation/
  decisions/
  risks/
  notes/
```

## Step Rules
- One step = one folder under `steps/`.
- Step folder name format: `NNNN-semantic-step-name`
- Use gaps such as `0010`, `0020`, `0030` to allow inserts later.
- Each step folder must contain `step.md`.
- Keep noisy step-local material inside the step folder instead of the plan root when the step starts generating artifacts.

Bad:
- `step-1.md`
- `draft-v2-final-final.md`
- `seam-fix-pass3-retry2.md`

Good:
- `0010-freeze-scope-lineage-and-contract-vocabulary`
- `0020-add-read-only-query-surface`
- `0030-emit-versioned-state-surfaces-and-issue-tickets`

## Stage Transition Rules
### Brainstorms -> Drafts
- Promote when exploration is stable enough to become implementation-shaped.
- Carry forward only the decisions, risks, contracts, and validation expectations that actually matter.

### Drafts -> InProgress
- Requires explicit user approval.
- Freeze the draft as the planning baseline.
- If the repo later adds a real `InProgress/` stage, create a fresh execution-shaped folder there.
- Until then, keep the draft folder as the source plan and track execution in the step content and validation artifacts.

### InProgress -> Completed
- Move only after implementation and validation evidence exist.
- Keep closeout artifacts with the completed plan folder.
- Do not rely on memory or old terminal output to reconstruct what was done.

## Engineering Constraints
Plans in this repo should assume small files, hard concern boundaries, and truthful runtime semantics.

### Python Rules
- Prefer small modules with one clear responsibility.
- Keep public interfaces typed.
- Keep IO and CLI glue at the edges.
- Separate command wiring from domain logic.
- Prefer explicit schema or contract objects at boundaries.
- Write tests around behavior and contracts, not around giant opaque integration flows only.

### File Size Rule
Code files should stay small.

Target guidance:
- ideal module size: `80-250` lines
- `>300` lines: smell, review the split immediately
- `300-600` lines: likely mixing concerns and should be reduced
- `>600` lines: do not normalize this; split unless there is a documented exception

Apply this rule to:
- Python modules
- CLI adapters
- workflow/controller modules
- contract modules
- query surfaces
- bridge or integration modules

If a planned change implies a large file, the step should state the intended split up front.

## Compiler / Plan Projection
Folderized plans can be compiled into a single reviewable Markdown projection inside the plan folder.

Compiler:
- `resources/plans/compile-plan.py`

Examples:
- `python resources/plans/compile-plan.py resources/plans/Drafts/bookforge-supervisable-engine`
- `python resources/plans/compile-plan.py resources/plans/Drafts/bookforge-supervisable-engine --dry-run --print-files`

Rules:
- The compiled file is a projection for review, not the source of truth.
- The folderized plan contents remain the source of truth.
- Draft plans being actively reviewed should usually keep a compiled projection.
- The compiler output must stay inside the selected plan folder.

## Template Usage
This repo does not yet have the full Nanda-style template pack.

Until templates are added:
1. start from an existing folderized draft plan
2. copy the folder into the target stage
3. rename it to a semantic slug
4. replace placeholder or inherited steps with real steps
5. keep step-local noise inside the step folder, not at the plan root

## Repo-Specific Guidance
- Plans should reference real repo files, commands, tests, and runtime contracts whenever possible.
- For BookForge engine work, keep the ownership split explicit:
  - BookForge owns prose generation and canonical workspace mutation.
  - External supervisor/operator systems should read state, decide, and supervise through explicit contracts rather than hidden inference.
- Do not describe a command as section-scoped if it silently falls back to a broader workflow family.
- Do not normalize mutable compatibility views as canonical lineage anchors when immutable run artifacts exist.
- Keep recovery, retry, and resume behavior explicit in the plan instead of implying that the runtime will do the right thing automatically.

## Legacy Material Rules
- `_Pinned/` exists because older planning work still contains important domain and implementation context.
- Treat `_Pinned/` as read-mostly reference material.
- Do not add new active plans there.
- If older loose plans are still valuable, migrate them intentionally into the folderized system instead of creating more loose-file drift.

## Commit Guidance
- For multi-step workstreams, prefer landing the plan baseline before starting deeper code changes.
- If a plan materially changes execution expectations, compile it and review the projection before implementation.
- Do not bundle unrelated legacy plan cleanup into a code-focused commit unless the cleanup is part of the plan step itself.
