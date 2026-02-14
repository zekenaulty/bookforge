# Change Log - Prompt Composition

## Usage
- Add one entry for every material change.
- Link to evidence artifacts (diffs, reports, tests).

## Entry Template
- timestamp:
- author:
- scope:
- changed_files:
- reason:
- expected_behavior_impact:
- verification_method:
- result:
- rollback_note:

## Entries

- timestamp: 2026-02-13T17:15:33-06:00
- author: Codex (GPT-5)
- scope: Story 0-4 execution (governance artifacts, composition implementation, integration, validation scaffolding)
- changed_files: resources/prompt_blocks/**; resources/prompt_composition/**; resources/prompt_templates/*.md; src/bookforge/prompt/composition.py; src/bookforge/workspace.py; scripts/validate_prompt_composition.py; scripts/validate_prompt_composition_controls.py; tests/test_prompt_composition.py
- reason: Execute approved prompt composition plan with semantic naming, manifest/allowlist contracts, and deterministic build validation.
- expected_behavior_impact: Runtime prompt loading remains flat-file; write/repair duplicate-weight rules are deduped per approved spans; composition failures now hard-fail on contract violations.
- verification_method: .venv/Scripts/python -m pytest tests/test_prompt_composition.py tests/test_workspace_init.py -q; .venv/Scripts/python scripts/validate_prompt_composition.py
- result: pass
- rollback_note: Revert resources/prompt_templates plus composition sources and restore pre-composition templates if contract regressions are detected.

- timestamp: 2026-02-13T17:15:33-06:00
- author: Codex (GPT-5)
- scope: Workflow hardening for update/init template distribution path
- changed_files: src/bookforge/workspace.py
- reason: Prevent write-permission coupling to repo resources by composing into per-book temporary build output.
- expected_behavior_impact: book init/update-templates still emits same flat prompt set, but no longer depends on mutating repo prompt_templates during workflow runs.
- verification_method: .venv/Scripts/python -m pytest tests/test_workspace_init.py -q
- result: pass
- rollback_note: Revert _copy_prompt_templates to repo-output composition if per-book build strategy conflicts with downstream tooling.

- timestamp: 2026-02-13T17:15:33-06:00
- author: Codex (GPT-5)
- scope: Encoding/newline policy hardening at repository level
- changed_files: .gitattributes
- reason: Enforce LF for prompt composition artifacts and related code to reduce CRLF churn risk.
- expected_behavior_impact: Git checkout/commit normalization aligns with UTF-8 LF contract for composition-critical files.
- verification_method: Manual review of .gitattributes + rerun scripts/validate_prompt_composition.py
- result: pass
- rollback_note: Remove path-specific eol rules if repository-level text normalization policy changes.
