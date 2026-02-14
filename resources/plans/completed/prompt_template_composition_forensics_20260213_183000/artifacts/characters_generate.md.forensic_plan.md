# Forensic Plan: characters_generate.md

## Snapshot
- Source: `resources/prompt_templates/characters_generate.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/characters_generate.md.snapshot.md`
- SHA256: `2F2EBE29BFBB7CBE823ED38BF2714E853B0C5FA41F65E47D3CD0217B4A97E85D`
- Line count: `139`
- Byte length: `5221`

## Code Touchpoints
- `src/bookforge\characters.py:658:    template = _resolve_template(book_root, "characters_generate.md")`
- `src/bookforge\workspace.py:50:    "characters_generate.md",`

## Change Set (Initial)
- Operation `O01`: Preserve full prompt semantics while moving to composition-managed source blocks.
  - Current span: `resources/prompt_templates/characters_generate.md:1-139`
  - Proposed replacement surface: `resources/prompt_blocks/phase/characters_generate.md` (generated into existing flat template path).
  - New language: `NO TEXT CHANGE` for this baseline operation.

## Prompt-to-Code Intent Notes
- This prompt is consumed through the touchpoints above; any block extraction must preserve the exact contract expected by those readers/parsers/validators.

## Risk Notes
- High-risk if this prompt emits JSON contracts consumed by schema validation or deterministic post-processors.
- All edits must remain semantically equivalent unless explicitly approved in follow-up review.
