# Outline Phase 04C-Intro - Character Intro Sync

Skill id: `bookforge.outline.intro-sync`
Kind: `phase`
Graph node: `outline.phase_04c_intro_sync`
Phase id: `phase_04c_intro_sync`
Logical phase: `phase_04_transition_causality_refinement`

## Purpose
- Repairs character intro fields after transition edits while leaving scenes unchanged.

## Prompt Contract
- Update only the targeted character intro fields and preserve the scene outline exactly.

## References
- `resources/prompt_blocks/phase/outline_pipeline/phase_04c_intro_sync_prompt_contract.md`
- `src/bookforge/phases/outline/phase_04c_intro_sync.py`
- `docs/help/outline_generate.md`
