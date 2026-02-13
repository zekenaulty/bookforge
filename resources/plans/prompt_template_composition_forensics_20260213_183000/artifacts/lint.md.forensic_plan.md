# Forensic Plan: lint.md

## Snapshot
- Source: `resources/prompt_templates/lint.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/lint.md.snapshot.md`
- SHA256: `047F798DEB6B553C1F03995D5356C0570B4A6FEE4CB61007E7CB1162C5E8DCBE`
- Line count: `156`
- Byte length: `6887`

## Code Touchpoints
- `src/bookforge/workspace.py:46`
- `src/bookforge/phases/lint_phase.py:239`
- Deterministic lint coupling:
  - `src/bookforge/phases/lint_phase.py:309-341`
  - `src/bookforge/pipeline/lint/tripwires.py:29-260`
  - `src/bookforge/pipeline/lint/helpers.py:10`

## Intent Summary
`lint.md` must stay aligned with deterministic lint add-ons and report normalization. Prompt structure changes can produce false confidence or conflict with enforced single-issue incoherence behavior.

## Detailed Change Plan (Span-Cited)

### Operation L01 - Preserve all policy rules verbatim in first migration pass
- Current span: `resources/prompt_templates/lint.md:1-73`
- Action: keep phase-local block with no semantic edits.

### Operation L02 - Preserve pass/fail JSON example blocks
- Current spans:
  - `resources/prompt_templates/lint.md:75-89`
- Action: keep examples unchanged.
- Note: duplicate braces/schema lines are intentional example pairs, not dedupe targets.

### Operation L03 - Preserve input placeholder block order
- Current span: `resources/prompt_templates/lint.md:91-156`
- Action: keep phase-local and verbatim.
- Coupling rationale:
  - `lint_phase` composes prompt values in this same conceptual order (`src/bookforge/phases/lint_phase.py:247-266`).

### Operation L04 - Optional shared extraction (no semantic delta)
- Candidate shared blocks (optional in first pass):
  - UI gate rule subsection `resources/prompt_templates/lint.md:11-15`
  - prose hygiene subsection `resources/prompt_templates/lint.md:22`
  - pipeline incoherent subsection `resources/prompt_templates/lint.md:44-51`
- Recommendation:
  - Defer extraction until second pass; keep first pass as no-op to avoid behavior drift.

## Proposed Composed Template Layout (Draft)
1. `lint/full_phase_body_v1` (first pass)
2. Optional second-pass split into `lint/policy_*` blocks after behavior lock test.

## Risk & Validation Notes
- Must not diverge from deterministic enforcement already in code (`pipeline_state_incoherent` single-issue clamp in `src/bookforge/phases/lint_phase.py:337-341`).
- Keep issue-code names unchanged to avoid downstream routing/report confusion.

## Reviewer Checklist
- Confirm no rewording in policy statements during pass 1.
- Confirm examples remain valid lint_report schema examples.
- Confirm placeholders remain present and unchanged.
