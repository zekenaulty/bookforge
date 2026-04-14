---
name: handoff-normalize
description: Normalizes terminal handoff and location-jump metadata for targeted scenes only.
metadata:
  skill_id: bookforge.outline.handoff-normalize
  display_name: Outline Phase 04C-Handoff - Handoff Normalize
  kind: phase
  graph_node: outline.phase_04c_handoff_normalize
  phase_id: phase_04c_handoff_normalize
  logical_phase: phase_04_transition_causality_refinement
---

# Outline Phase 04C-Handoff - Handoff Normalize

Use this skill when the task belongs to `outline.phase_04c_handoff_normalize` in the BookForge skill tree.

Prompt contract
- Normalize the allowed handoff fields for the targeted refs without changing scene order or scene identity.

Output
- JSON matching the outline_handoff_normalize_v1 contract
