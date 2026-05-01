# Fragment Assignment Rules

Date: 2026-04-29

## Purpose

This note captures the deterministic assignment model for outline timeline splitting.

The rule is conservative:

> Do not assign an artifact to active branch state unless there is structural evidence. If evidence is weak, preserve it as salvage or quarantine.

## Evidence Strength

### High Confidence

Use for active inclusion by default.

- artifact path directly belongs to a selected immutable source run
- artifact path directly belongs to a selected frozen projection
- fragment declares matching `source_run_id`
- normalized section hash matches the candidate exactly
- normalized scene list hash matches the candidate exactly
- scene ids and section/chapter refs match exactly and no competing candidate matches

### Medium Confidence

Eligible only when the split plan allows medium-confidence inclusion.

- character/thread set matches candidate and conflicts with other candidates
- prose metadata summary matches candidate scene summary/outcome
- phase history refs match candidate scene ids after renumbering
- mtime falls inside the candidate wave and structure matches

### Low Confidence

Do not include in active branch state by default.

- mtime adjacency only
- filename scope only
- partial character-name match without stable id
- prose text appears thematically related but lacks metadata

### Ambiguous

Quarantine or salvage.

- artifact plausibly belongs to more than one candidate
- source run absent and hashes do not match
- state file references characters from multiple candidate timelines

### Conflict

Quarantine and block validation until resolved.

- artifact declares a different source run than candidate
- artifact has branch/node coordinates from another branch
- artifact includes entity ids absent from selected timeline
- artifact matches multiple incompatible candidates at high confidence

## Assignment Outputs

Every considered artifact receives one assignment record:

- `included`
- `excluded`
- `quarantined`
- `salvage_reference`
- `ambiguous`
- `conflict`
- `missing`

No hidden skip is allowed. If the system sees a relevant file, it must explain what happened to it.

## Veiled Ledger Implication

For Veiled Ledger, this means the system should be able to say:

- which sections belong to the declared source-run timeline
- which sections belong to the section-draft wave
- which prose/state/character artifacts cannot be trusted
- which artifacts can be reused only as salvage/reference
- which branch needs redraft before it can be semantically valid

The author agent can then choose or auto-select a timeline, but it should not invent the artifact assignment.
