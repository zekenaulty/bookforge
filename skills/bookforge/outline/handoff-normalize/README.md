# Outline Phase 04C-Handoff - Handoff Normalize

Skill id: `bookforge.outline.handoff-normalize`
Kind: `phase`
Graph node: `outline.phase_04c_handoff_normalize`
Phase id: `phase_04c_handoff_normalize`
Logical phase: `phase_04_transition_causality_refinement`

## Purpose
- Normalizes terminal handoff and location-jump metadata for targeted scenes only.

## Prompt Contract
- Normalize the allowed handoff fields for the targeted refs without changing scene order or scene identity.

## References
- `resources/prompt_blocks/phase/outline_pipeline/phase_04c_handoff_normalize_prompt_contract.md`
- `src/bookforge/phases/outline/phase_04c_handoff_normalize.py`
- `docs/help/outline_generate.md`
