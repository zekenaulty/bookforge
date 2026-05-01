# Steps Index

| Step | Status | Depends On | Outcome |
| --- | --- | --- | --- |
| 0010-audit-current-file-backed-evidence | designed | - | Produce a concrete inventory of current evidence files, contracts, emitters, and Nanda evidence needs. |
| 0020-define-sqlite-schema-and-evidence-contract | designed | 0010 | Freeze the first book/workspace ledger schema, ID rules, freshness/status rules, and Python contract boundaries. |
| 0030-implement-ledger-store-and-idempotent-backfill | designed | 0020 | Add SQLite store plus backfill from current supervision/recovery histories. |
| 0040-dual-write-execution-recovery-author-and-artifact-evidence | designed | 0030 | Wire current emitters to write file artifacts and ledger rows consistently, including author asset actions. |
| 0050-add-evidence-query-surfaces-and-cli | designed | 0040 | Expose operation/receipt/artifact/scope/branch evidence through Python query and CLI JSON. |
| 0060-add-reader-anchor-and-citation-evidence | designed | 0050 | Make prose/reader selections provenance-backed and mutation-safety aware. |
| 0070-add-nanda-consumption-fixtures-and-contract-docs | designed | 0060 | Provide fixture data and docs for Nanda response capsules, action cards, branch transitions, and recovery workbench. |
| 0080-reserve-vector-and-external-store-adapters | designed | 0070 | Document deferred vector/external DB adapter boundaries without implementing them prematurely. |
