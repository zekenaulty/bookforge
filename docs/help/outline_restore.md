# bookforge outline restore

Purpose
- Restore `outline/outline.json` from either:
  - a pipeline run id, or
  - a backup snapshot directory created by `outline backup`.

Usage
- `bookforge outline restore --book <id> [--run-id <run_id> | --backup-path <path>] [--overwrite-current] [--set-latest-run-pointer]`

Scope
- Requires `--book`.
- Provide exactly one of `--run-id` or `--backup-path`.

Required parameters
- `--book`: Book id slug.

Optional parameters
- `--run-id`: Restore from this run folder in `outline/pipeline_runs/<run_id>/`.
- `--backup-path`: Restore from a backup folder (absolute path or workspace-relative path).
- `--overwrite-current`: Overwrite `outline.json` in place. If omitted, current outline is archived as `outline_vN.json` and `chapters_vN/`.
- `--set-latest-run-pointer`: When source includes a known run id, update latest run/report pointers to that run.
- `--workspace`: Override workspace root (global option).

Outputs
- Writes refreshed:
  - `outline/outline.json`
  - `outline/chapters/ch_###.json`
  - `outline/characters.json`
  - `outline/threads.json`
- Optionally updates:
  - `outline/pipeline_latest.json`
  - `outline/outline_pipeline_latest.json`
  - `outline/outline_pipeline_report_latest.json`

Notes
- Restored outline is normalized and schema-validated before write.
- Default behavior is safe archive-first restore (unless `--overwrite-current`).

Examples
- Restore from run id and repoint latest run:
  - `bookforge --workspace workspace outline restore --book my_novel_v1 --run-id 20260216_234528 --set-latest-run-pointer`
- Restore from backup directory:
  - `bookforge --workspace workspace outline restore --book my_novel_v1 --backup-path backups/outline_completed/my_novel_v1/20260216_234528_20260217_030314`
- Force in-place overwrite:
  - `bookforge --workspace workspace outline restore --book my_novel_v1 --run-id 20260216_234528 --overwrite-current`
