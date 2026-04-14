# Outline Phase 04C - Metadata Relink

Skill id: `bookforge.outline.metadata-relink`
Kind: `phase`
Graph node: `outline.phase_04c_metadata_relink`
Phase id: `phase_04c_metadata_relink`
Logical phase: `phase_04_transition_causality_refinement`

## Purpose
- Repairs structural relink drift after transition insertion without authoring new scenes.

## Prompt Contract
- Relink metadata within the allowed window and keep structural edits inside the permitted field set.

## References
- `resources/prompt_blocks/phase/outline_pipeline/phase_04c_metadata_relink_prompt_contract.md`
- `src/bookforge/phases/outline/phase_04c_metadata_relink.py`
- `docs/help/outline_generate.md`
