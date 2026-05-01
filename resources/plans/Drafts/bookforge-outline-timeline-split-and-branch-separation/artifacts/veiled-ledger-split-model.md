# Veiled Ledger Split Model

Date: 2026-04-29

## Working Hypothesis

Veiled Ledger appears to contain at least two outline timelines:

1. the declared/frozen outline lineage
2. the section-draft or recovery wave that bled into later materialization

There may also be ambiguous prose/state artifacts that are useful as inspiration but unsafe as active branch state.

## Desired Operator Experience

The author agent should be able to say:

```text
I found two outline timelines.

Candidate A is anchored to source run <id> and covers scopes <...>.
Candidate B is anchored to section-draft wave <id/timestamp> and covers scopes <...>.

These artifacts are cleanly assigned.
These artifacts are ambiguous and will be preserved as salvage only.
These state/character files conflict.

Recommended action: create separated branches, validate each branch, then choose the timeline to redraft/promote.
```

If only one valid candidate remains after validation, the author agent can auto-select it. If two candidates are structurally coherent but imply different books, it must ask the user which timeline is correct.

## Branches Produced

Example names:

- `split/veiled-ledger/declared-source-run`
- `split/veiled-ledger/section-draft-wave`
- `split/veiled-ledger/salvage`

The salvage branch/bucket is not a canonical candidate. It exists to preserve useful prose or ideas that should not contaminate active state.

## Scope Of Work Shape

For each candidate:

- active outline to materialize
- active frozen projections
- section scope coverage
- prose to keep
- prose to invalidate
- state/projections to keep
- state/projections to quarantine
- redraft scopes
- validation gates
- downstream scopes to review

## Repair Flow After Split

The split system stops at isolated branches.

Then existing recovery/story-weaving tools take over:

1. validate split branch
2. convert split branch to recovery plan
3. quarantine/invalidate/rebuild as needed
4. redraft impacted chapters/sections
5. semantic/downstream review
6. promotion approval

## Key Safety Rule

Creating a split branch does not mean the branch is clean.

It means the branch is isolated and explainable. Cleanliness requires validation receipts.
