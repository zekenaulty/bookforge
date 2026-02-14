# Forensic Plan: appearance_projection.md

## Snapshot
- Source: `resources/prompt_templates/appearance_projection.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/appearance_projection.md.snapshot.md`
- SHA256: `EF863DD5ED891E5B300A56570216752AB98A5E6B6800AE84C302D670FE906E34`
- Line count: `31`
- Byte length: `930`

## Code Touchpoints
- `src/bookforge\characters.py:317:    template = _resolve_template(book_root, "appearance_projection.md")`

## Change Set (Initial)
- Operation `O01`: Preserve full prompt semantics while moving to composition-managed source blocks.
  - Current span: `resources/prompt_templates/appearance_projection.md:1-31`
  - Proposed replacement surface: `resources/prompt_blocks/phase/appearance_projection.md` (generated into existing flat template path).
  - New language: `NO TEXT CHANGE` for this baseline operation.

## Prompt-to-Code Intent Notes
- This prompt is consumed through the touchpoints above; any block extraction must preserve the exact contract expected by those readers/parsers/validators.

## Risk Notes
- High-risk if this prompt emits JSON contracts consumed by schema validation or deterministic post-processors.
- All edits must remain semantically equivalent unless explicitly approved in follow-up review.
