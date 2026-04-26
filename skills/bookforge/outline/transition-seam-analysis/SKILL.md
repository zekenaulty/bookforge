---
name: transition-seam-analysis
description: Analyze transition seams and select required repair or insertion candidates.
metadata:
  skill_id: bookforge.outline.transition-seam-analysis
  display_name: Outline Transition Seam Analysis
  kind: outline_phase
  graph_node: outline.phase_04a_transition_seam_analysis
  phase_id: phase_04a_transition_seam_analysis
  logical_phase: phase_04_transition_causality_refinement
---

# Outline Transition Seam Analysis

Use this skill when the task belongs to `outline.phase_04a_transition_seam_analysis` in the BookForge skill tree.

Prompt contract
- Return one chapter payload plus a phase_report with candidate_seams.

Output
- valid phase_04a transition analysis JSON
