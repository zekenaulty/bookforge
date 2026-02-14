# Forensic Plan: output_contract.md

## Snapshot
- Source: `resources/prompt_templates/output_contract.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/output_contract.md.snapshot.md`
- SHA256: `1AB0A9DD99C0DB33C0AABFF9439D3877457A07A9230A1A5E3A08099BC1AC33E4`
- Line count: `21`
- Byte length: `1959`

## Code Touchpoints
- `src/bookforge/workspace.py:53`
- `src/bookforge/workspace.py:303`
- `src/bookforge/workspace.py:347`
- System prompt assembly coupling:
  - `src/bookforge/prompt/system.py:8-24`

## Intent Summary
`output_contract.md` defines cross-phase output constraints at system level. It must remain stable and concise.

## Detailed Change Plan (Span-Cited)

### Operation OC01 - Preserve full body exactly
- Current span: `resources/prompt_templates/output_contract.md:1-21`
- Action: move as single block `resources/prompt_blocks/system/output_contract_v1.md`.
- Replacement language: `NO TEXT CHANGE`.

### Operation OC02 - Optional shared extraction
- Candidate span:
  - global continuity array rule: `resources/prompt_templates/output_contract.md:19-21`
- Recommendation: keep local in pass 1 to avoid accidental divergence with system-level contract scope.

## Risk & Validation Notes
- This file is injected into every system prompt; drift here is global.
- Any wording change requires explicit multi-phase regression review.

## Reviewer Checklist
- Confirm composed output exactly matches source text.
- Confirm system prompt generation still includes this section unchanged.
