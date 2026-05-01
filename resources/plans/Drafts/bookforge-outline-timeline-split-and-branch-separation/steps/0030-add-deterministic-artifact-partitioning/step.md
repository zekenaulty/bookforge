# 0030 - Add Deterministic Artifact Partitioning

Status: draft
Depends On: 0020

## Objective

Assign non-outline artifacts to timeline candidates, or explicitly quarantine them, using deterministic evidence.

This is the step that turns "two outlines exist" into "these exact files belong to candidate A, these belong to candidate B, and these are ambiguous."

## Detailed Work

- Add artifact collectors for:
  - prose scene files
  - scene metadata
  - phase history
  - chapter markdown
  - character indexes
  - character state
  - continuity summaries
  - context projections
  - appearance and setting projections
  - recovery/supervision receipts where useful
- Add assignment rules:
  - direct source-run/scope link is high confidence
  - exact normalized section/scene hash match is high confidence
  - character/thread set plus scene structure match is medium confidence
  - mtime adjacency alone is low confidence
  - mismatch against two candidates is conflict
  - no reliable evidence is ambiguous
- Emit partition records:
  - path
  - artifact class
  - assignment status
  - candidate id
  - confidence
  - evidence refs
  - reason codes
- Keep destructive decisions out of this step.

## Files Likely Touched

- `src/bookforge/query/outline_timeline_split.py`
- `src/bookforge/query/branches.py` if artifact classes need refinement
- `tests/test_outline_timeline_split_partition.py`

## Tests

- Prose matching one candidate is assigned high confidence.
- Ghost character state goes to the candidate that declares the character id.
- Duplicate protagonist/ghost character conflicts are flagged.
- Artifacts with only mtime evidence are not assigned active state.
- Ambiguous artifacts are not silently included.

## Definition Of Done

- Every collected artifact has an assignment record.
- Every assignment has evidence and confidence.
- Only high and selected medium-confidence artifacts are eligible for active branch materialization.
- Ambiguous and conflict artifacts are visible to Nanda as salvage/quarantine candidates.
