# bookforge book show-current

Status
- Not implemented yet (CLI returns "Not implemented yet.").

Purpose
- Show the current book selection.

Usage
- bookforge book show-current [--format text|json]

Optional parameters
- --format: Output format (text or json).
- --workspace: Override workspace root (global option).

Examples
- Minimal:
  bookforge book show-current
- With optional parameters:
  bookforge --workspace workspace book show-current --format json