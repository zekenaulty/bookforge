# Acceptance

This plan is ready for promotion only when the target implementation can satisfy all of the following:

- BookForge exposes workflow, lineage, integrity, and book state through stable read-only query modules.
- BookForge can resolve observer-shaped scope selection into a current `TimelineNodeRef` without hand-reading raw workspace files.
- `ScopeSelector` can explicitly address `main`, a derived branch, or a fork group without relying on inferred scope alone.
- At least one real execution path emits:
  - a book-rooted versioned `StateSurface`
  - categorized `IssueTicket` output
  - a truthful pause/result status
- Every emitted contract object carries a `TimelineNodeRef`.
- One narrow `ExecutionRequest -> ExecutionResult` path can be executed and verified on `main` without hidden scope switching.
- Lineage validation runs before section materialization or resume proceeds.
- Provider exhaustion can be observed as `retryable_pause` or `hard_fail` without reading raw transport logs.
- Branch reruns can execute in isolation without mutating canonical state directly.
- Fork-group assembly and single-branch promotion are explicitly distinct merge operations with validation gates.
- Assembly does not write provisional state to `main` before validation completes.
- Derived branches expose unambiguous current-node state through branch-local pointers or manifests.
- Fork-group assembly refuses when the frozen parent snapshot is no longer valid for safe merge.
- The plan states clearly how branch lifecycle states map to public execution results and canonical-change status.
- Contaminated book recovery is expressed as composable branch-first primitives, not a one-off fixer command.
- Recovery promotion can apply removals/quarantine as well as additions/replacements.
- Nanda can build a `book_timeline_impact_report_v1` from BookForge evidence and then request scoped recovery/story-weaving actions without direct filesystem mutation.
- A recovered book can be verified through query surfaces as no longer blocked by the original lineage or chimera issue.
- Help docs and CLI labels match the actual runtime mode and recovery behavior.
- New code follows the small-file rule and does not normalize `300-600` line modules as acceptable.
