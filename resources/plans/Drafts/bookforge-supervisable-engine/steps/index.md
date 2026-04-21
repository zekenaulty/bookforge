# Steps Index

| Step | Status | Depends On | Outcome |
| --- | --- | --- | --- |
| 0010-freeze-scope-lineage-and-contract-vocabulary | draft | - | Freeze runtime vocabulary, artifact truth rules, and caller-visible scope semantics. |
| 0020-add-read-only-query-surface | draft | 0010 | Expose workflow, lineage, integrity, character, and continuity reads through small query modules. |
| 0030-emit-versioned-state-surfaces-and-issue-tickets | draft | 0010, 0020 | Emit engine-owned state, pause, and issue surfaces after execution. |
| 0040-add-truthful-scoped-execution-and-bounded-resume | draft | 0010, 0020, 0030 | Support one narrow same-mode execution/resume path with truthful result reporting. |
| 0050-harden-reconciliation-integrity-and-command-surface | draft | 0030, 0040 | Add post-execution reconciliation, stronger integrity helpers, and help-doc coherence. |
