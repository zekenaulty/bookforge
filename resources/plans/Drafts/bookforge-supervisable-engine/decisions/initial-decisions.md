# Initial Decisions

- BookForge remains the only system allowed to generate prose or mutate canonical book state.
- Nanda will consume BookForge truth; it should not have to reverse-engineer hidden runtime mode from raw files forever.
- Thin outline, deep outline, section-local outline, section write, and recovery import are distinct runtime modes and may not silently promote into one another.
- Immutable outline run artifacts and frozen chapter projections are the preferred lineage anchors.
- Mutable compatibility artifacts such as `outline.json` are never sufficient by themselves to justify scoped materialization.
- Query modules belong under `src/bookforge/query/` and must remain read-only.
- Shared engine contract objects belong under `src/bookforge/contracts/`.
- The first truthful supervised issue class is lineage/integrity conflict, because it is both mechanical and already proven by live failures.
- Existing Gemini `T1 -> T2` carry should be preserved and instrumented lightly; do not build a second thought lineage graph unless evidence demands it.
- Help docs are part of the contract surface. If the docs imply broader scope than the runtime actually executes, that is a defect.
