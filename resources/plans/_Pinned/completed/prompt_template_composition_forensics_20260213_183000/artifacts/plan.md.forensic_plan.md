# Forensic Plan: plan.md

## Snapshot
- Source: `resources/prompt_templates/plan.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/plan.md.snapshot.md`
- SHA256: `DBA2419A902A4FF9A078EAB1744D4A40E190AE778AA01FE06BC5D5855641942D`
- Line count: `92`
- Byte length: `3604`

## Code Touchpoints
- `src/bookforge/workspace.py:43`
- `src/bookforge/phases/plan.py:65-68`
- Schema and normalization coupling:
  - `src/bookforge/phases/plan.py:24`
  - `src/bookforge/phases/plan.py:335-430`
  - `src/bookforge/phases/plan.py:593`

## Intent Summary
`plan.md` defines scene-card output constraints. It is tightly coupled to `scene_card` schema normalization.

## Detailed Change Plan (Span-Cited)

### Operation P01 - Preserve scene-card JSON contract language exactly
- Current span: `resources/prompt_templates/plan.md:1-92`
- Action: keep as single phase-local block in first pass.
- Replacement language: `NO TEXT CHANGE`.

### Operation P02 - Optional second-pass extraction candidates
- Candidate spans (deferred):
  - ui_allowed contract language (if duplicated elsewhere)
  - output-shape reminder blocks
- Recommendation: defer until after composition baseline is proven stable.

## Risk & Validation Notes
- Any drift can break normalization assumptions in `_normalize_scene_card`.
- Must preserve wording around required/optional fields and cardinality.

## Reviewer Checklist
- Confirm no semantic changes to scene-card required keys/rules.
- Confirm compatibility with `SCENE_CARD_SCHEMA_VERSION` and validation flow.
