# Risk Log - Prompt Composition

## Usage
- Add or update entries whenever risk status changes.

## Entry Template
- timestamp:
- risk_id:
- risk_statement:
- trigger:
- impact:
- likelihood:
- mitigation:
- owner:
- status:
- evidence:

## Entries

- timestamp: 2026-02-13T17:15:33-06:00
- risk_id: R-001
- risk_statement: Ambiguous naming causes semantic drift.
- trigger: Non-semantic source names in production composition paths.
- impact: Human mis-edits and cross-phase drift.
- likelihood: medium
- mitigation: Approved semantic rename map promoted into resources/prompt_blocks with manifest semantic_id enforcement.
- owner: Composition owner
- status: mitigated
- evidence: resources/prompt_blocks/**; resources/prompt_composition/manifests/*.composition.manifest.json

- timestamp: 2026-02-13T17:15:33-06:00
- risk_id: R-002
- risk_statement: Unknown placeholders ship.
- trigger: Token typo or untracked placeholder in compiled prompt.
- impact: Runtime substitution failures and silent contract drift.
- likelihood: medium
- mitigation: prompt_tokens_allowlist.json + hard-fail unknown token detection in composition.py.
- owner: Composer owner
- status: mitigated
- evidence: resources/prompt_composition/prompt_tokens_allowlist.json; src/bookforge/prompt/composition.py

- timestamp: 2026-02-13T17:15:33-06:00
- risk_id: R-003
- risk_statement: Dedupe changes alter model behavior.
- trigger: Approved write/repair repetition removal.
- impact: Potential behavioral weighting change.
- likelihood: medium
- mitigation: Story 5 behavioral baseline + thresholds still required before production sign-off.
- owner: Validation owner
- status: open
- evidence: resources/plans/prompt_template_composition_plan_20260213_183000.md (Story 5)

- timestamp: 2026-02-13T17:15:33-06:00
- risk_id: R-005
- risk_statement: Encoding drift breaks determinism.
- trigger: BOM/CRLF variance between fragments and compiled outputs.
- impact: checksum churn and hidden prompt drift.
- likelihood: medium
- mitigation: UTF-8(no BOM)+LF enforcement in composer and validation script.
- owner: Composer owner
- status: mitigated
- evidence: src/bookforge/prompt/composition.py; scripts/validate_prompt_composition.py

- timestamp: 2026-02-13T17:15:33-06:00
- risk_id: R-009
- risk_statement: Composer version skew causes checksum churn.
- trigger: Composition outputs differ from approved source-of-truth checksums.
- impact: review noise and potential unreviewed drift.
- likelihood: low
- mitigation: source_of_truth_checksums.json + enforce_checksums validation.
- owner: Tooling owner
- status: mitigated
- evidence: resources/prompt_composition/source_of_truth_checksums.json; src/bookforge/prompt/composition.py

- timestamp: 2026-02-13T17:15:33-06:00
- risk_id: R-005
- risk_statement: Encoding drift breaks determinism.
- trigger: Git newline conversion between LF and CRLF.
- impact: checksum churn and composition contract drift.
- likelihood: low
- mitigation: Added .gitattributes LF enforcement for composition-critical paths.
- owner: Composer owner
- status: mitigated
- evidence: .gitattributes
