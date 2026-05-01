# Initial Decisions

## Decision: Successor Plan, Not Umbrella Extension
`bookforge-supervisable-engine` has completed its substrate role. Capability projection is a successor plan because it serves Nanda-facing self-description rather than adding more core execution machinery.

## Decision: Projection Is Static
Capability projection reports what BookForge supports. It does not report whether a specific selected scene, section, branch, or recovery scope is ready now. Dynamic readiness remains a separate scope-specific query.

## Decision: Macro Workflows Are Recipes
Macro workflows may remain useful, but they must expose child actions and should not be treated as rails for the author agent. The author agent may choose legal primitives adaptively.

## Decision: No Full MCP Server Yet
The projection should be compatible with future MCP-style tooling, but this plan does not build the protocol server. The first milestone is machine-readable BookForge capability truth.

## Decision: Receipts Beat Persona
Execution receipts and query surfaces are evidence. Thought signatures and author persona context may help explanation or recovery, but they do not prove capability support or execution state.
