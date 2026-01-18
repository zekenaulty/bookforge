# bookforge run

Purpose
- Run the plan/write/lint/repair loop for a book.

Usage
- bookforge run --book <id> [--steps <n>] [--until <chapter:scene>] [--resume]

Scope
- Requires book scope (explicit --book or current book).

Required parameters
- --book: Book id slug.

Optional parameters
- --steps: Number of loop iterations to run.
- --until: Stop condition, e.g. chapter:3 or chapter:3:scene:2.
- --resume: Resume a prior run.
- --workspace: Override workspace root (global option).

Examples
- Minimal:
  bookforge run --book my_novel_v1
- With optional parameters:
  bookforge --workspace workspace run --book my_novel_v1 --steps 10 --until chapter:3 --resume
