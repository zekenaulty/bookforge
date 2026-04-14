---
name: transition-seam-analysis
description: Finds transition seam candidates and proposes required transition resolutions.
metadata:
  skill_id: bookforge.outline.transition-seam-analysis
  display_name: Outline Phase 04A - Transition Seam Analysis
  kind: phase
  graph_node: outline.phase_04a_transition_seam_analysis
  phase_id: phase_04a_transition_seam_analysis
  logical_phase: phase_04_transition_causality_refinement
---

# Outline Phase 04A - Transition Seam Analysis

Use this skill when the task belongs to `outline.phase_04a_transition_seam_analysis` in the BookForge skill tree.

Prompt contract
- Analyze the scene draft for seam failures and emit candidate transition fixes with routing-ready metadata.

Output
- JSON matching the transition_refine_v1 seam-analysis contract
