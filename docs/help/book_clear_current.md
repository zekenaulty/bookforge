# bookforge book clear-current

Status
- Not implemented yet (CLI returns "Not implemented yet.").

Purpose
- Clear the current book selection.

Usage
- bookforge book clear-current [--force]

Optional parameters
- --force: Skip confirmation if interactive mode is added later.
- --workspace: Override workspace root (global option).

Examples
- Minimal:
  bookforge book clear-current
- With optional parameters:
  bookforge --workspace workspace book clear-current --force