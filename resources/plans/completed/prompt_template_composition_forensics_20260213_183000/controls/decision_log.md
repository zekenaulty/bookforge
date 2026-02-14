# Decision Log - Prompt Composition

## Usage
- Record all policy, scope, architecture, and implementation decisions.

## Entry Template
- timestamp:
- decision_id:
- decision:
- context:
- options_considered:
- selected_option:
- rationale:
- impact_scope:
- risks_accepted:
- follow_up:

## Entries

- timestamp: 2026-02-13T17:15:33-06:00
- decision_id: D-001
- decision: Promote forensic proposed_refactor_v1 fragments into production composition sources with approved semantic names.
- context: User approved naming taxonomy lock and requested plan execution.
- options_considered: Keep review-only fragments; re-author new fragments manually; promote with semantic rename map.
- selected_option: Promote with semantic rename map.
- rationale: Preserves reviewed text while enforcing semantic source identity.
- impact_scope: resources/prompt_blocks/**; resources/prompt_composition/manifests/**
- risks_accepted: Source span metadata is fragment-span based in pass 1, not original snapshot offsets.
- follow_up: Tighten span provenance format in next pass if required by reviewers.

- timestamp: 2026-02-13T17:15:33-06:00
- decision_id: D-002
- decision: Enforce composition contracts during template copy/update flow.
- context: Story 3 requires compose-before-copy while keeping runtime loading flat-file.
- options_considered: Compose only in CI; compose on update-templates/init; pre-generate and never compose in workflow.
- selected_option: Compose on template copy/update.
- rationale: Prevents stale flat templates from drifting away from manifested source-of-truth.
- impact_scope: src/bookforge/workspace.py
- risks_accepted: update/init now fail-fast on composition contract violations.
- follow_up: Add command-level UX guidance if failures become noisy.

- timestamp: 2026-02-13T17:15:33-06:00
- decision_id: D-003
- decision: Introduce separate validation scripts for composition contracts and control-log enforcement.
- context: Plan requires deterministic + governance gates before release.
- options_considered: Unit-tests only; scripts only; both scripts and tests.
- selected_option: Both scripts and tests.
- rationale: Scripts provide CI entry points; tests provide regression coverage.
- impact_scope: scripts/validate_prompt_composition.py; scripts/validate_prompt_composition_controls.py; tests/test_prompt_composition.py
- risks_accepted: Control-log script uses changed-file hints and cannot infer VCS diff context by itself.
- follow_up: Wire changed-file inputs from CI git diff command.

- timestamp: 2026-02-13T17:15:33-06:00
- decision_id: D-004
- decision: Compose into per-book temporary output directory during workspace template copy operations.
- context: Repo-resource writes are brittle in installed/read-only environments.
- options_considered: Compose directly into resources/prompt_templates; compose to per-book temporary directory then copy.
- selected_option: Compose to per-book temporary directory then copy.
- rationale: Preserves runtime flat-file behavior while removing repo write dependency.
- impact_scope: src/bookforge/workspace.py
- risks_accepted: Report artifacts are produced by dedicated validation command, not every init/update invocation.
- follow_up: Keep scripts/validate_prompt_composition.py as canonical artifact-generation gate.

- timestamp: 2026-02-13T17:15:33-06:00
- decision_id: D-005
- decision: Add repository .gitattributes LF rules for prompt composition and control-log surfaces.
- context: Git reported pending CRLF conversion warnings on critical files.
- options_considered: rely on local git config; enforce path-level eol=lf rules.
- selected_option: enforce path-level eol=lf rules.
- rationale: Keeps encoding/newline policy deterministic across collaborators and CI.
- impact_scope: .gitattributes
- risks_accepted: Existing contributors may need renormalization when first pulling these rules.
- follow_up: Run git add --renormalize . if line-ending churn appears in future PRs.
