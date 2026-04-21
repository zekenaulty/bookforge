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
