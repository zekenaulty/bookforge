# Steps Index

| Step | Status | Depends On | Outcome |
| --- | --- | --- | --- |
| 0010-freeze-scope-lineage-and-contract-vocabulary | completed | - | Freeze runtime vocabulary, coordinate primitives, artifact truth rules, and caller-visible scope semantics. |
| 0020-add-read-only-query-surface | completed | 0010 | Expose workflow, lineage, integrity, character, continuity, and scope-to-node resolution through small query modules. |
| 0030-emit-versioned-state-surfaces-and-issue-tickets | completed | 0010, 0020 | Emit book-rooted state, pause, and issue contracts that carry timeline coordinates. |
| 0040-add-truthful-scoped-execution-and-bounded-resume | completed | 0010, 0020, 0030 | Support one narrow main-branch resume path with expected-node validation and truthful pause reporting. |
| 0045-add-isolated-branch-reruns-and-fork-group-assembly | completed | 0030, 0040 | Add branch isolation, sibling fork groups, promotion vs assembly semantics, and validation-gated merge paths. |
| 0050-harden-reconciliation-integrity-and-command-surface | completed | 0030, 0040, 0045 | Add post-execution and post-promotion reconciliation, stronger integrity helpers, and help-doc coherence. |
| 0060-extract-minimal-engine-execution-surface-for-nanda | completed | 0050 | Replace command-only orchestration with a smaller action catalog and legal-next-action API that Nanda can compose. |
