# Prompt Composition Change Matrix (20260213_183000)

| Prompt | Risk | Primary Consumer | Planned Text Delta | Detailed Artifact |
|---|---|---|---|---|
| `appearance_projection.md` | Medium | `src/bookforge/characters.py:317` | None (phase-local block extraction only) | `artifacts/appearance_projection.md.forensic_plan.md` |
| `author_generate.md` | Low | `src/bookforge/author.py:21` | None | `artifacts/author_generate.md.forensic_plan.md` |
| `characters_generate.md` | Medium | `src/bookforge/characters.py:658` | None (initial pass) | `artifacts/characters_generate.md.forensic_plan.md` |
| `continuity_pack.md` | Medium | `src/bookforge/phases/continuity_phase.py:31` | None (initial pass) | `artifacts/continuity_pack.md.forensic_plan.md` |
| `lint.md` | High | `src/bookforge/phases/lint_phase.py:239` | None in pass 1; optional structured extraction pass 2 | `artifacts/lint.md.forensic_plan.md` |
| `outline.md` | Medium | `src/bookforge/outline.py:367-370` | None (initial pass) | `artifacts/outline.md.forensic_plan.md` |
| `output_contract.md` | High | `src/bookforge/workspace.py:303,347` | None in pass 1 | `artifacts/output_contract.md.forensic_plan.md` |
| `plan.md` | High | `src/bookforge/phases/plan.py:65-68` | None in pass 1 | `artifacts/plan.md.forensic_plan.md` |
| `preflight.md` | High | `src/bookforge/phases/preflight_phase.py:32` | Shared-block extraction only; no language change | `artifacts/preflight.md.forensic_plan.md` |
| `repair.md` | Critical | `src/bookforge/phases/repair_phase.py:35` | Deduplicate repeated reconciliation blocks; no policy semantic change | `artifacts/repair.md.forensic_plan.md` |
| `state_repair.md` | Critical | `src/bookforge/phases/state_repair_phase.py:37` | Shared-block extraction only; no language change | `artifacts/state_repair.md.forensic_plan.md` |
| `style_anchor.md` | Medium | `src/bookforge/runner.py:372` | None | `artifacts/style_anchor.md.forensic_plan.md` |
| `system_base.md` | Critical | `src/bookforge/workspace.py:302,346` | None in pass 1 | `artifacts/system_base.md.forensic_plan.md` |
| `write.md` | Critical | `src/bookforge/phases/write_phase.py:35` | Deduplicate repeated `must_stay_true` line; preserve all core rules | `artifacts/write.md.forensic_plan.md` |

## Notes
- "None" means no semantic text change; only migration to composition-managed source blocks.
- Deduplication actions are explicitly listed in each high-risk artifact with span-level citations.
