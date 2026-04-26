---
name: metadata-relink
description: Relink metadata in constrained scene windows after transition insertions.
metadata:
  skill_id: bookforge.outline.metadata-relink
  display_name: Outline Metadata Relink
  kind: outline_phase
  graph_node: outline.phase_04c_metadata_relink
  phase_id: phase_04c_metadata_relink
  logical_phase: phase_04_transition_causality_refinement
---

# Outline Metadata Relink

Use this skill when the task belongs to `outline.phase_04c_metadata_relink` in the BookForge skill tree.

Prompt contract
- Return only allowed metadata field changes for the active relink window.

Output
- valid phase_04c metadata relink JSON
