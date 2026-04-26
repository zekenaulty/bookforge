---
name: seam-hygiene
description: Repair seam hygiene in constrained outline windows after relinking.
metadata:
  skill_id: bookforge.outline.seam-hygiene
  display_name: Outline Seam Hygiene
  kind: outline_phase
  graph_node: outline.phase_04d_seam_hygiene
  phase_id: phase_04d_seam_hygiene
  logical_phase: phase_04_transition_causality_refinement
---

# Outline Seam Hygiene

Use this skill when the task belongs to `outline.phase_04d_seam_hygiene` in the BookForge skill tree.

Prompt contract
- Return only allowed seam fields for the active hygiene window.

Output
- valid phase_04d seam hygiene JSON
