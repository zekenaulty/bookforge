# Steps Index

| Step | Status | Depends On | Outcome |
| --- | --- | --- | --- |
| 0010-define-outline-fragment-graph-and-scope-of-work | draft | - | Freeze the graph vocabulary and `OutlineFragmentScopeOfWork` contract. |
| 0020-add-read-only-timeline-split-preview | draft | 0010 | Produce deterministic timeline candidates and scope-of-work previews without mutation. |
| 0030-add-deterministic-artifact-partitioning | draft | 0020 | Assign prose/state/projection artifacts to candidate timelines or quarantine with confidence. |
| 0040-create-separated-outline-timeline-branches | draft | 0030 | Materialize selected candidates as isolated branches with manifests and receipts. |
| 0050-add-validation-and-recovery-handoff | draft | 0040 | Validate split branches and convert them into existing recovery/redraft workflows. |
| 0060-project-capabilities-and-nanda-fixtures | draft | 0050 | Expose query/action capabilities and Nanda fixtures for author-agent operation. |
