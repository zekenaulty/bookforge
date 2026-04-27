# Initial Risks

- `src/bookforge/cli.py`, `src/bookforge/section_workflow.py`, and `src/bookforge/runner.py` already carry broad responsibilities and can easily absorb too much more.
- A "scoped" execution adapter may secretly depend on batch assumptions and accidentally normalize a hidden workflow-family switch.
- Query helpers may drift into mutation or implicit repair if the read-only boundary is not enforced.
- Mutable compatibility artifacts may continue to look canonical unless lineage classification is made explicit in both code and docs.
- Provider retry/backoff behavior may remain buried in transport logs if pause state is not elevated into a first-class result surface.
- If `TimelineNodeRef` is under-specified, later branch and assembly features will bolt on incompatible addressing rules and recreate lineage drift in a more formal-looking shape.
- If branch promotion and fork-group assembly are not separated early, future parallel writing work will reuse single-branch promotion logic and silently merge incompatible sibling outputs.
- If sibling branches can read one another during fan-out execution, merge order will become a hidden dependency and parallelism will stop being trustworthy.
- If book-rooted surfaces are implemented as ad hoc aggregation over many tiny artifacts, callers will still be forced to infer canonical truth from storage layout.
- Derived prose features can sprawl into expensive or low-signal machinery if introduced before the state and ticket contracts are stable.
- The repo already contains older and newer planning shapes; without discipline, this plan can become another disconnected artifact instead of the local BookForge source of truth.

## Current Residual Risks (2026-04-27)
- The supervision substrate is now stronger than the product-output layer. Compile/export, manuscript validation, preview gates, and word/page count enforcement remain underpowered compared with the new execution/action surfaces.
- Recovery primitives are structurally useful, but Nanda still needs impact-report, planner, and approval-loop implementation to use them as a real author agent rather than as manual CLI tools.
- Semantic review is diagnostic evidence assembly in BookForge, not story proof. If the author pane treats diagnostic findings as final judgment, it will overclaim.
- Lint/repair depth is safer at `8`, but routing is still coarse. Without lane routing, high-cost full repair/state-repair remains the default for many failures.
- Series-level state exists in scaffolding and character canon support, but cross-book rollups and series continuity validation remain incomplete.
- The old `_Pinned` backlog is useful but noisy. Pulling whole old plans forward would reintroduce stale assumptions; each useful item needs a new scoped plan.
