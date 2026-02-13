# Stability Report (proposed_refactor_v1)

## Guardrails
- No runtime prompt-loading behavior changed in this proposal package.
- `write.md` and `repair.md` are the only prompts with textual edits; edits are dedupe-only.
- All other prompts are composition-layout changes only (semantic no-op).
- Known malformed wrapped lines are intentionally unchanged for risk containment in pass 1.

## Text-Change Scope
- `write.md`: removed duplicate lines at 24,65,68,71,81,105,155,158,194,197.
- `repair.md`: removed duplicate ranges 55-58,60-63,65-68,82-85,87-90,108-111,134-137,189-192,194-197.
- Everything else: no semantic text change proposed.
