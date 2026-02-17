# bookforge outline backup

Purpose
- Capture a recoverable backup of a run-derived, schema-valid outline state.
- Optionally include the full source run artifact folder for audit and replay.

Usage
- `bookforge outline backup --book <id> [--run-id <run_id>] [--output-dir <path>] [--allow-non-success] [--skip-run-artifacts]`

Scope
- Requires `--book`.

Required parameters
- `--book`: Book id slug.

Optional parameters
- `--run-id`: Source run id. Defaults to latest outline run pointer.
- `--output-dir`: Backup root directory. Default: `workspace/backups/outline_completed/<book_id>/`.
- `--allow-non-success`: Allow backup even when source run status is not `SUCCESS`/`SUCCESS_WITH_WARNINGS`.
- `--skip-run-artifacts`: Back up only normalized outline snapshot files, not the full `pipeline_run` copy.
- `--workspace`: Override workspace root (global option).

Outputs
- Creates backup folder:
  - `workspace/backups/outline_completed/<book_id>/<run_id>_<timestamp>/`
- Writes:
  - `outline_snapshot/outline.json`
  - `outline_snapshot/chapters/ch_###.json`
  - `outline_snapshot/characters.json`
  - `outline_snapshot/threads.json`
  - `outline_snapshot/outline.draft.user.json` (if present)
  - `outline_snapshot/location_registry_active.json` (if present)
  - `pipeline_run/*` (unless `--skip-run-artifacts`)
  - `backup_manifest.json`
- Updates pointers:
  - `workspace/books/<book_id>/outline/outline_backup_latest.json`
  - `workspace/books/<book_id>/outline/outline_backups_index.json`

Notes
- Backup content is rebuilt from run handoff artifacts and validated against outline schema before snapshot.
- This command does not modify the active `outline.json`.

Examples
- Back up latest successful run:
  - `bookforge --workspace workspace outline backup --book my_novel_v1`
- Back up a specific run id:
  - `bookforge --workspace workspace outline backup --book my_novel_v1 --run-id 20260216_234528`
- Back up snapshot only (no pipeline run copy):
  - `bookforge --workspace workspace outline backup --book my_novel_v1 --skip-run-artifacts`
