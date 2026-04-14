---
name: intro-sync
description: Repairs character intro fields after transition edits while leaving scenes unchanged.
metadata:
  skill_id: bookforge.outline.intro-sync
  display_name: Outline Phase 04C-Intro - Character Intro Sync
  kind: phase
  graph_node: outline.phase_04c_intro_sync
  phase_id: phase_04c_intro_sync
  logical_phase: phase_04_transition_causality_refinement
---

# Outline Phase 04C-Intro - Character Intro Sync

Use this skill when the task belongs to `outline.phase_04c_intro_sync` in the BookForge skill tree.

Prompt contract
- Update only the targeted character intro fields and preserve the scene outline exactly.

Output
- JSON matching the outline_intro_sync_v1 contract
