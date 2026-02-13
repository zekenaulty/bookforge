# Forensic Plan: system_base.md

## Snapshot
- Source: `resources/prompt_templates/system_base.md`
- Snapshot: `resources/plans/prompt_template_composition_forensics_20260213_183000/snapshots/system_base.md.snapshot.md`
- SHA256: `DC70F4A84F6FDDDFB491A123D23B26A7CC7AC2B860363178A09B12FA606E862A`
- Line count: `32`
- Byte length: `4114`

## Code Touchpoints
- `src/bookforge/workspace.py:52`
- `src/bookforge/workspace.py:302`
- `src/bookforge/workspace.py:346`
- System prompt assembly:
  - `src/bookforge/prompt/system.py:8-24`

## Intent Summary
`system_base.md` is global authority text merged into `system_v1.md` and therefore affects every phase. Any drift here has highest blast radius.

## Detailed Change Plan (Span-Cited)

### Operation SB01 - Preserve full body exactly (first migration pass)
- Current span: `resources/prompt_templates/system_base.md:1-32`
- Action: move as a single block `resources/prompt_blocks/system/system_base_v1.md`.
- Replacement language: `NO TEXT CHANGE`.

### Operation SB02 - Optional second-pass shared extraction
- Candidate extraction spans (deferred):
  - Prose hygiene rule: `resources/prompt_templates/system_base.md:15`
  - UI gate rule: `resources/prompt_templates/system_base.md:20`
  - JSON contract baseline: `resources/prompt_templates/system_base.md:24-26`
- Recommendation: defer to avoid changing precedence interpretation.

## Coupling Notes
- This text is concatenated as the `## Base Rules` section by `build_system_prompt` (`src/bookforge/prompt/system.py:8-24`).
- It is copied/regenerated via `update_book_templates` (`src/bookforge/workspace.py:333-349`).

## Risk & Validation Notes
- High risk: even punctuation-level edits can alter model priority behavior.
- First pass should be a strict no-op extraction.

## Reviewer Checklist
- Verify no line changes between original and composed output.
- Verify generated `system_v1.md` remains equivalent under same author/constitution inputs.
