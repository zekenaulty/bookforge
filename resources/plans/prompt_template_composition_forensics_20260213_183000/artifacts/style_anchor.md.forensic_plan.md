# Forensic Plan: style_anchor.md

## Snapshot
- Source: `resources/prompt_templates/style_anchor.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/style_anchor.md.snapshot.md`
- SHA256: `1047A314F8AE316FA22A06546BD7CF680262505D35D6CFCDF8E1180971DDE0F1`
- Line count: `10`
- Byte length: `365`

## Code Touchpoints
- `src/bookforge\workspace.py:51:    "style_anchor.md",`
- `src/bookforge\runner.py:372:    template = _resolve_template(book_root, "style_anchor.md")`
- `src/bookforge\memory\continuity.py:79:    return book_root / "prompts" / "style_anchor.md"`

## Change Set (Initial)
- Operation `O01`: Preserve full prompt semantics while moving to composition-managed source blocks.
  - Current span: `resources/prompt_templates/style_anchor.md:1-10`
  - Proposed replacement surface: `resources/prompt_blocks/phase/style_anchor.md` (generated into existing flat template path).
  - New language: `NO TEXT CHANGE` for this baseline operation.

## Prompt-to-Code Intent Notes
- This prompt is consumed through the touchpoints above; any block extraction must preserve the exact contract expected by those readers/parsers/validators.

## Risk Notes
- High-risk if this prompt emits JSON contracts consumed by schema validation or deterministic post-processors.
- All edits must remain semantically equivalent unless explicitly approved in follow-up review.
