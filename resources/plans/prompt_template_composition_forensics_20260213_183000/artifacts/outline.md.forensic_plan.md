# Forensic Plan: outline.md

## Snapshot
- Source: `resources/prompt_templates/outline.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/outline.md.snapshot.md`
- SHA256: `5CC31E096D85313344F8030EEF1CBC5CA2539EAE7AD5625E9FF0A3FE31452848`
- Line count: `157`
- Byte length: `4747`

## Code Touchpoints
- `src/bookforge\workspace.py:42:    "outline.md",`
- `src/bookforge\outline.py:367:    book_template = book_root / "prompts" / "templates" / "outline.md"`
- `src/bookforge\outline.py:370:    return repo_root(Path(__file__).resolve()) / "resources" / "prompt_templates" / "outline.md"`

## Change Set (Initial)
- Operation `O01`: Preserve full prompt semantics while moving to composition-managed source blocks.
  - Current span: `resources/prompt_templates/outline.md:1-157`
  - Proposed replacement surface: `resources/prompt_blocks/phase/outline.md` (generated into existing flat template path).
  - New language: `NO TEXT CHANGE` for this baseline operation.

## Prompt-to-Code Intent Notes
- This prompt is consumed through the touchpoints above; any block extraction must preserve the exact contract expected by those readers/parsers/validators.

## Risk Notes
- High-risk if this prompt emits JSON contracts consumed by schema validation or deterministic post-processors.
- All edits must remain semantically equivalent unless explicitly approved in follow-up review.
