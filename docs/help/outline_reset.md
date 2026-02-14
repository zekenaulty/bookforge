# bookforge outline reset

Purpose
- Archive and/or reset outline generation artifacts for a clean rerun cycle.

Usage
- bookforge outline reset --book <id> [--archive] [--keep-working-outline-artifacts]
- bookforge outline reset --book <id> [--clear-generated-outline | --no-clear-generated-outline]
- bookforge outline reset --book <id> [--clear-pipeline-runs | --no-clear-pipeline-runs]
- bookforge outline reset --book <id> [--dry-run] [--force]

Scope
- Requires explicit `--book`.
- Operates only on outline-related artifacts under `workspace/books/<book>/outline`.

Required parameters
- --book: Book id slug.

Optional parameters
- --archive: Archive selected outline targets before reset.
- --keep-working-outline-artifacts: Keep working outline files in place after archive/reset.
- --clear-generated-outline: Remove generated outline working artifacts (default: true).
- --no-clear-generated-outline: Keep generated outline working artifacts.
- --clear-pipeline-runs: Remove outline pipeline run artifacts and metadata (default: true).
- --no-clear-pipeline-runs: Keep outline pipeline run artifacts and metadata.
- --dry-run: Preview actions without mutating files.
- --force: Proceed even if an outline run lock/pause marker exists.
- --workspace: Override workspace root (global option).

Behavior
- Writes a reset report and marker into the outline folder.
- When `--archive` is set, archive output path is printed in CLI output.
- `--dry-run` reports what would be removed/preserved without changing files.

Outputs
- `workspace/books/<book>/outline/outline_reset_report.json`
- `workspace/books/<book>/outline/outline_reset_marker.json`
- Optional archive directory (when `--archive` is enabled).

Examples
- Dry-run preview:
  - `bookforge outline reset --book my_novel_v1 --dry-run`
- Archive and reset:
  - `bookforge outline reset --book my_novel_v1 --archive`
- Archive only while preserving working outline artifacts:
  - `bookforge outline reset --book my_novel_v1 --archive --keep-working-outline-artifacts --no-clear-generated-outline`
