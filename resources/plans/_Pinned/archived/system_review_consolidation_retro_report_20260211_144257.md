# System Review Consolidation Report (20260211_144257)

Scope
Alignment analysis between `resources/plans/archived/original/bookforge_plan_v2.md` and the current system state. This includes:
- What must be updated in the original plan to align with reality.
- What items are already covered or made obsolete by recent work.
- What new targets exist that were not in the original plan.

Executive Summary
The system has significantly evolved beyond the original v2 plan in the direction of durable state, preflight alignment, continuity guardrails, and prompt hardening. Core loop, provider abstraction, schema governance, and author/outline/characters generation exist. However, several v2 milestones remain partially implemented or absent (opening preview gate, duplication/similarity checks, compile/export commands, prompt registry snapshots, and full rerun semantics). New durable systems (inventory/plot devices, appearance/DCAS) and prompt schema hardening are major additions that must be incorporated into the updated plan.

Current System Snapshot (high‑level)
- CLI commands exist for init, author generate, outline generate, characters generate, run, book set/show/reset/update-templates, compile, export synopsis. Compile/export are stubbed with _not_implemented in `src/bookforge/cli.py`.
- Phases exist: plan, preflight, continuity pack, write, repair, state_repair, lint.
- Durable state added: item_registry, plot_devices, transfer_updates, inventory_alignment_updates, durable commit ledger, scope gating.
- Appearance system added (DCAS): appearance_current/history, APPEARANCE_CHECK in prompts, projection refresh.
- Prompt system and templates are now heavily hardened with JSON contracts and invalid/valid examples.
- Prompt budgeter exists; prompt registry loader exists.
- Continuity pack exists and is used in write/state_repair.

Alignment Against v2 Definition of Done (condensed)

Met or Largely Met
- CLI scaffolding and LLM provider abstraction.
- Workspace layout with book.json, state.json, outline, canon, draft, logs, prompts.
- Series-level canon scaffolding.
- Author creation/versioned author library + pinned versions.
- Prompt templates per phase and stable system prompt assembly.
- Continuity pack generation and usage in the writing loop.
- Plan/write/lint/repair loop with schema validation, state patches, and rerun safety.

Partially Met / Needs Update
- Prompt registry snapshots + prompt hash logging (registry loader exists but snapshots/logging incomplete).
- Prompt budgeter reporting exists; budgeter enforcement + deterministic size reporting partly implemented (needs verification against plan expectations).
- Rerun semantics and versioned outputs are partially implemented via reset/update-templates but not full append-only/immutable rules.
- Docs/help exist but may be stale relative to new durable systems (inventory/plot devices/appearance).

Not Met / Missing
- Opening preview gate, banned phrase injection, and similarity checks.
- Compile/export synopsis implementation (CLI stubs only).
- Explicit duplication prevention gates beyond lint warnings.
- Word/page count enforcement per scene.
- Full logging coverage (prompt hashes, budget outcomes, registry snapshots) as described in v2.

What Must Be Updated in the Original Plan
1) Add durable state systems to the plan scope:
   - item_registry / plot_devices schemas and update logic.
   - transfer_updates + inventory_alignment_updates with scope policy enforcement.
   - durable commit ledger / snapshots.

2) Add preflight state alignment as a first‑class phase:
   - Scope gate rules (timeline/ontological scope).
   - Preflight posture alignment constraints + expected_before rules.

3) Add DCAS (appearance system) to canon/state/prompt layers:
   - appearance_base in canon, appearance_current/history in runtime.
   - APPEARANCE_CHECK authoritative surface.
   - projection refresh step and attire boundary rules.

4) Add prompt schema hardening requirements:
   - “JSON contract blocks” shared across all phases.
   - Conflict rules like registry vs transfer and expected_before alignment.

5) Update lint design to reflect:
   - pre/post state candidate logic.
   - pipeline_state_incoherent guard.
   - authoritative surfaces and timeline scope reasoning.

6) Update plan for phase modularization already performed:
   - phases/ separation of plan/preflight/write/repair/state_repair/lint.
   - pipeline modules for prompts, parsing, durable logic, and state application.

What is Obsolete or Already Covered by Recent Work
- Some v2 anti‑duplication ideas are now less urgent because the system emphasizes continuity packs, state primacy, and lint‑repair loops. However, they are not replaced and should be re‑evaluated rather than deleted.
- The original plan’s simplistic canon store expectations are superseded by the durable inventory/plot device registries and DCAS. Update to reflect the richer canon state architecture.

New Targets Not Covered in v2
- Durable inventory + plot device registries and transfer semantics.
- Scope‑aware mutation enforcement (non‑real/non‑present gating + override).
- Appearance system (DCAS) and authorative appearance checks.
- Prompt schema hardening plan and meta‑validation rules.
- Pipeline state coherence checks (pre/post, pipeline_state_incoherent guard).
- LLM lint timeline reasoning (durable vs ephemeral, last occurrence wins).

Outstanding Work (non‑test/bugfix)
- `resources/plans/series_continuity_plan.md` (still outstanding).
- Incorporate `resources/plans/proposed/chatgpt_suggested_wins.md` into refined plans where applicable.
- Opening preview gate + banned phrase and similarity checks (Story 10 in v2).
- Lint/repair similarity gates (Story 11 in v2) still incomplete.
- Canon store/retrieval (Story 12), compile/export (Story 13), rerun controls (Story 14), logging/metrics (Story 15), tests/docs (Story 16) remain partially implemented or not implemented.

Recommended Plan Updates (high‑level)
- Create BookForge v3 plan that explicitly includes:
  - Durable state systems (items/devices/transfers) and scope policy.
  - Preflight alignment phase and its schema contracts.
  - DCAS appearance system and authorative appearance surfaces.
  - Prompt schema hardening requirements as a formal deliverable.
  - Lint pipeline coherency constraints (pre/post candidate state agreement).
- Retain original v2 targets but mark non‑implemented stories as pending: preview gate, similarity checks, compile/export, rerun controls, logging/metrics, and tests/docs.

References Consulted
- `resources/plans/archived/original/bookforge_plan_v2.md`
- `src/bookforge/cli.py`
- `src/bookforge/phases/*`
- `schemas/*.json`
- `docs/help/*`
- `resources/prompt_templates/*`

Notes
- This report does not cover bug/issue triage; it focuses on plan alignment and scope drift.
- The current system has outgrown v2’s assumptions; updating the original plan is necessary to avoid engineering against obsolete targets.

