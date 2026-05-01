# Nanda Author Agent Handoff

Date: 2026-04-29

## Purpose

This plan gives Nanda a tool shape for reasoning about outline bleed without relying on user observation or LLM guessing.

Nanda should reason and communicate. BookForge should graph, split, mutate, validate, and receipt.

## Expected Nanda Flow

1. User asks about chimera/outline bleed/timeline repair.
2. Nanda calls `outline_timeline_split_preview`.
3. Nanda explains candidate timelines and confidence.
4. If one valid candidate exists, Nanda can auto-select.
5. If multiple candidates imply different books, Nanda asks the user to choose.
6. Nanda calls `create_outline_timeline_split_branches`.
7. Nanda inspects branch manifests, diff, artifact index, and validation.
8. Nanda creates or recommends a recovery/redraft work plan from the selected branch.

## Author Response Rules

Acceptable:

```text
BookForge found two deterministic outline timelines. Candidate A is anchored to the declared source run. Candidate B is anchored to a later section-draft wave. Five artifacts are ambiguous and will be preserved as salvage, not active state.
```

Not acceptable:

```text
I fixed the timeline.
```

unless execution receipts prove branch creation, validation, recovery, redraft, and promotion.

## Tool Truth

The author agent should not claim:

- a branch is clean because it was created
- ambiguous data was removed unless a receipt says so
- a timeline is the correct story unless the user/author policy selected it
- prose is repaired because outline artifacts were split

The author agent can claim:

- candidates found
- evidence and confidence
- selected or auto-selected anchor
- branch creation result
- validation state
- remaining required work

## UI/Action Card Needs

Nanda action cards should show:

- preview-only vs mutation
- selected candidate id
- confidence
- branch names to create
- ambiguous artifact count
- conflict count
- approval requirement
- expected receipts
- next recovery action
