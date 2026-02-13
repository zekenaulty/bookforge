# Forensic Plan: author_generate.md

## Snapshot
- Source: `resources/prompt_templates/author_generate.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/author_generate.md.snapshot.md`
- SHA256: `E87899515FC1F1139FBDAEC81E6237B895E60F6912576EB33B47F5C44039146D`
- Line count: `51`
- Byte length: `1278`

## Code Touchpoints
- `src/bookforge\author.py:21:AUTHOR_TEMPLATE = repo_root(Path(__file__).resolve()) / 'resources' / 'prompt_templates' / 'author_generate.md'`

## Change Set (Initial)
- Operation `O01`: Preserve full prompt semantics while moving to composition-managed source blocks.
  - Current span: `resources/prompt_templates/author_generate.md:1-51`
  - Proposed replacement surface: `resources/prompt_blocks/phase/author_generate.md` (generated into existing flat template path).
  - New language: `NO TEXT CHANGE` for this baseline operation.

## Prompt-to-Code Intent Notes
- This prompt is consumed through the touchpoints above; any block extraction must preserve the exact contract expected by those readers/parsers/validators.

## Risk Notes
- High-risk if this prompt emits JSON contracts consumed by schema validation or deterministic post-processors.
- All edits must remain semantically equivalent unless explicitly approved in follow-up review.
