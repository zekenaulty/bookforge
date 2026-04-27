# 2026-04-27 0081 Downstream Review Impacts

## Summary
- Extended `get_recovery_blast_radius(...)` with diagnostic downstream review impacts.
- Manifest-declared downstream prose artifacts now appear under the `downstream_review` family.
- These impacts report:
  - `artifact_status: diagnostic`
  - `safe_as_canonical: false`
  - `mutation_supported: false`
  - `recommended_action: author_review_downstream_scope`

## Boundary
- This does not add semantic downstream dependency tracing.
- This does not make downstream prose an automatic invalidation/redraft target.
- It only gives Nanda a truthful list of declared downstream artifacts that should be reviewed after recovery.

## Why
- Downstream chapters may remain structurally clean but continuity-unsafe after upstream recovery.
- Nanda needs visible review candidates without BookForge overstepping into broad mutation.

## Validation
- Focused suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' tests/test_recovery_actions.py --basetemp=.pytest_tmp_0081_downstream_review_focus`
  - Result: `6 passed`
- Full suite passed:
  - `.\.venv\Scripts\python.exe -m pytest -o addopts='' --basetemp=.pytest_tmp_0081_downstream_review_full`
  - Result: `310 passed`
