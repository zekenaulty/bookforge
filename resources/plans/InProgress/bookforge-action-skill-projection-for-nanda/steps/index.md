# Steps Index

| Step | Status | Depends On | Outcome |
| --- | --- | --- | --- |
| 0010-audit-current-action-query-readiness-surfaces | completed | - | Inventory real BookForge public surfaces and identify which are capabilities, readiness checks, macros, diagnostics, or internal helpers. |
| 0015-map-nanda-surface-api-needs | completed | 0010 | Cross-reference Nanda plans, FastAPI routes, and UI affordances to the BookForge surfaces/APIs they need. |
| 0020-define-unit-boundary-and-capability-contract | completed | 0010, 0015 | Freeze capability descriptor vocabulary, unit boundary doctrine, mutation classes, and projection contract. |
| 0030-generate-projection-from-existing-surfaces | completed | 0020 | Build the projection from real action/query/readiness sources with stale-surface tests. |
| 0040-expose-projection-through-python-and-cli | completed | 0030 | Add Python and CLI JSON surfaces for Nanda and operators. |
| 0050-add-nanda-consumption-fixture | completed | 0040 | Emit representative fixture output and tests for Nanda capability-registry ingestion. |
| 0060-document-nanda-and-mcp-style-skill-mapping | completed | 0050 | Document how BookForge capability truth maps to Nanda buckets and later MCP-style skills. |
