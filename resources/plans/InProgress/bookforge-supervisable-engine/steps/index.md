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
| 0070-segment-section-write-into-scoped-scene-actions | completed | 0060 | Turn the hidden `section_write` batch flow into truthful scene-phase actions and readiness queries that Nanda can traverse as an author skill graph. |
| 0071-make-scene-and-section-write-execution-branch-scoped | completed | 0070 | Move scene and section write execution off `main` into real branch-local execution roots so old-scene rewrites and isolated author work become truthful. |
| 0072-add-parent-target-promotion-rebase-and-parallel-fork-write | completed | 0071 | Let branch work merge upward into parent branches or `main`, add explicit rebase, and support sibling parallel write branches with validation-gated assembly. |
| 0075-extract-appearance-setting-and-context-refinement-surfaces | completed | 0070 | Make character appearance, scene background/setting, and prior-stage T1 thought-signature context explicit queryable projection layers instead of incidental prompt side effects. |
| 0080-add-outline-lineage-audit-and-recovery-briefing | completed | 0020, 0030, 0050, 0060 | Add read-only outline lineage audit, section-level lineage matrix, stale artifact inventory, and recovery candidate briefing so Nanda can localize chimera risks before any repair mutation. |
