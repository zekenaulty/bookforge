# Acceptance

This plan is ready for promotion only when the target implementation can satisfy all of the following:

- BookForge exposes workflow, lineage, integrity, and book state through stable read-only query modules.
- At least one real execution path emits:
  - a versioned `StateSurface`
  - categorized `IssueTicket` output
  - a truthful pause/result status
- One narrow `ExecutionRequest -> ExecutionResult` path can be executed and verified without hidden scope switching.
- Lineage validation runs before section materialization or resume proceeds.
- Provider exhaustion can be observed as `retryable_pause` or `hard_fail` without reading raw transport logs.
- Help docs and CLI labels match the actual runtime mode and recovery behavior.
- New code follows the small-file rule and does not normalize `300-600` line modules as acceptable.
