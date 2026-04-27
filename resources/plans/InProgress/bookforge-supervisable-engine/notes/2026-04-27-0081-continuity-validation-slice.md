# 2026-04-27 0081 Continuity Validation Slice

## Summary
- Added recovery-branch validation for continuity-family artifacts before promotion.
- `validate_recovery_branch` now scans:
  - `draft/context/continuity_pack.json`
  - `draft/context/continuity_history/*.json`
  - `draft/context/bible.md`
  - `draft/context/last_excerpt.md`
  - affected `draft/context/chapter_seams/ch_*/**/*.json`
- The validator blocks promotion when those artifacts retain:
  - character references that are absent from the normalized branch outline
  - stale `THREAD_*` references when the normalized outline exposes thread IDs
  - stale embedded `node.branch_id` or `selector.branch_id` values in JSON artifacts

## Boundary
- This is structural validation only.
- It prevents obvious ghost timeline continuity from surviving a recovery branch.
- It does not decide whether rebuilt continuity prose is narratively complete or good.

## Why
- Continuity artifacts can stay stale even when outline, prose, and character state have been normalized.
- Nanda needs these blockers reported through validation receipts before it can safely recommend promotion.

## Validation
- Focused suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' tests/test_recovery_actions.py --basetemp=.pytest_tmp_0081_continuity_validation_focus`
  - Result: `4 passed`
- Full suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_continuity_validation_full`
  - Result: `308 passed`
