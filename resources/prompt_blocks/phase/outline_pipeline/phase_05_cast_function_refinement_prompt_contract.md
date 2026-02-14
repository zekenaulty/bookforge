# OUTLINE PIPELINE PHASE 05: CAST FUNCTION REFINEMENT

You are refining cast architecture and role utility in the outline.
Return ONLY a single JSON object. No markdown, no code fences, no commentary.
Use strict JSON (double quotes, no trailing commas).

Required output schema:
{
  "schema_version": "cast_refine_v1",
  "outline": {
    "schema_version": "1.1",
    "chapters": []
  },
  "cast_report": {
    "core_character_ids": [],
    "supporting_character_ids": [],
    "episodic_character_ids": [],
    "recurring_without_job_count": 0,
    "edits_applied": []
  }
}

Goal:
- Ensure recurring characters have clear causal jobs.
- Clean introduction integrity (first appearance, introduces arrays, intro stubs).
- Avoid cast bloat by merging/demoting weak roles.

Rules:
- A recurring character should appear in >= 3 scenes unless explicitly justified.
- A recurring character must cause at least one concrete outcome.
- Do not keep cameo-only recurring characters.
- Prefer role merge or demotion over adding new characters.
- Keep character_id and thread_id stability.
- Keep chapter/section/scene ordering stable unless necessary for cast integrity.

Introduction rules:
- A character can be introduced once.
- introduces arrays must match first appearance.
- character.intro must match first scene appearance.

Output expectations:
- outline contains the cast-refined v1.1 outline.
- cast_report summarizes classification and edits.

Transition-refined outline (phase 04):
{{outline_transitions_refined_v1_1}}

Book:
{{book}}

Targets:
{{targets}}

Notes:
{{notes}}

