# 0040 Expose Projection Through Python And CLI

Status: completed
Depends On: 0030

## Goal
Expose the capability projection through stable Python and CLI JSON surfaces so Nanda and operators can consume it without importing private modules.

## Detailed Work
- Export capability projection from `bookforge.query`.
- Add CLI command, likely one of:
  - `bookforge capabilities --json`
  - `bookforge workflow capabilities --json`
- Support optional scope parameters only if they do not blur dynamic readiness into the static projection.
- If a scope is provided, CLI may include links to readiness commands, but should not inline a dynamic readiness verdict unless explicitly named as a readiness command.
- Emit JSON that is stable enough for Nanda tests.
- Ensure command help distinguishes:
  - capability projection
  - legal-next-action discovery
  - readiness checks
  - execution actions

## Likely Files Touched
- `src/bookforge/cli.py`
- `src/bookforge/query/__init__.py`
- `docs/help/workflow.md` or related help docs if present
- `tests/test_cli_capabilities.py`

## Tests
- CLI returns valid JSON.
- CLI output schema matches Python query shape.
- CLI does not require a live book for static projection unless a concrete source dependency is unavoidable.
- CLI help does not imply that static capability equals scope-specific readiness.

## Definition Of Done
- Nanda can call a stable CLI or Python surface to get engine capability truth.
- Static projection and dynamic readiness command surfaces are clearly separated in help text.
- CLI fixture is deterministic enough for cross-repo consumption tests.
