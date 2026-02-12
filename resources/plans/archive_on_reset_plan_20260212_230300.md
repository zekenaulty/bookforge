# Archive-On-Reset Plan (20260212_230300)

## Purpose
Add an optional `--archive` flag to the reset command that copies all reset-purged artifacts into a workspace-level archive folder before any deletion. If the archive cannot be created or validated, reset must abort with no data loss.

## Scope
- Applies to `book reset` only.
- Archives are stored outside the book folder: `workspace/archives/<book_id>/reset_<timestamp>_<short_hash>/...`.
- Default mode: **copy**. Optional `--archive-mode move` for power users.
- Logs are optional: `--archive-logs` includes `logs/llm` + `logs/runs`. Default excludes logs.

## Requirements
- Archive creation must succeed **before** deletion.
- Reset must fail (no deletion) if archive creation/validation fails.
- Archive keeps full relative paths for easy cross-run comparison.
- Archive manifest is always written for traceability.

## Proposed CLI
- `bookforge --workspace <ws> book reset --book <id> --archive`
- Optional:
  - `--archive-mode copy|move` (default: copy)
  - `--archive-logs` (default: false)

## Archive Structure
```
workspace/archives/<book_id>/reset_YYYYMMDD_HHMMSS_<short_hash>/
  draft/context/...
  draft/chapters/...
  logs/llm/...      (only if --archive-logs)
  logs/runs/...     (only if --archive-logs)
  archive_manifest.json
```

## Archive Manifest (archive_manifest.json)
Fields:
- timestamp
- book_id
- archive_mode
- include_logs
- purge_paths (relative)
- sizes (bytes)
- tool_version (optional)
- git_commit (optional)

## Implementation Plan
### Story 1: Identify reset purge targets and build a stable purge list
- Locate reset implementation (likely in `src/bookforge/workspace/reset.py` or similar).
- Enumerate all paths reset deletes today:
  - `draft/context/*`
  - `draft/chapters/*`
  - `logs/llm/*` (if `--archive-logs`)
  - `logs/runs/*` (if `--archive-logs`)
  - any pause markers or temp artifacts
- Ensure purge list is deterministic and only contains existing paths.

### Story 2: Archive creation + validation (copy default)
- Create archive root: `workspace/archives/<book_id>/reset_<timestamp>_<short_hash>/`.
- Copy all purge paths into archive root preserving relative paths.
- Write `archive_manifest.json` after copy completes.
- Validation rule: archive root exists + manifest exists + each top-level copied path exists.
- If any validation fails: abort reset with non-zero error; do not delete.

### Story 3: Reset delete step (only after validation)
- Perform existing reset deletions (same purge list).
- If deletion fails, report failure but keep archive intact.

### Story 4: Logging / UX
- Log archive path and manifest path in console output.
- Log counts (files/dirs) and size summary if cheap to compute.

## Edge Cases
- Very large archives: allow `--archive-mode move` for faster operation.
- Partial copy failures: must abort reset without deleting.
- Symlinks: decide to copy link target or link itself (document behavior).
- Archive name collisions: add short hash to guarantee uniqueness.

## Definition of Done
- `--archive` creates an archive folder with expected paths and manifest.
- Reset aborts safely when archive fails to create/validate.
- `--archive-logs` includes `logs/llm` + `logs/runs`; default excludes logs.
- Default mode is copy; optional move works.

## Status Tracker
- Story 1: Not started
- Story 2: Not started
- Story 3: Not started
- Story 4: Not started

## Notes
- Keep archives outside `workspace/books/<book_id>` as requested.
- Default to copy for safety; move is opt-in.
