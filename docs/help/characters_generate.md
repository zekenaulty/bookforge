# bookforge characters generate

Purpose
- Expand outline character stubs into canon character entries and per-book character state.
- Seed inventory, containers, and invariants so writing has grounded character state.

Usage
- bookforge characters generate --book <id> [--count <n>]

Scope
- Requires explicit --book (current-book selection is not implemented).
- Reads outline/characters.json (or outline.json characters array) and series canon if present.
- Does not invent new characters; it expands only the outline-provided stubs.
- If not run manually, it is executed implicitly before writing starts.

Required parameters
- --book: Book id slug.

Optional parameters
- --count: Optional limit on the number of outline characters to refine.
- --workspace: Override workspace root (global option).

Outputs
- Writes series canon:
  - workspace/series/<series_id>/canon/characters/<slug>/character.json
  - Updates workspace/series/<series_id>/canon/index.json
- Writes per-book state:
  - workspace/books/<book>/draft/context/characters/<slug>.state.json
  - Updates workspace/books/<book>/draft/context/characters/index.json
- Updates state.json with characters status.

Notes
- Inventory is tracked per character and per container.
- Held items must specify hand_left or hand_right.
- Container contents should be explicit (e.g., satchel contents).

Examples
- Minimal:
  bookforge characters generate --book my_novel_v1
- With optional parameters:
  bookforge --workspace workspace characters generate --book my_novel_v1 --count 6

Scoping
- Character state changes are recorded per chapter/scene via state_patch.character_updates.
