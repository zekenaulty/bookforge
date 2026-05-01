# bookforge book intent

Purpose
- Promote an author-only seed into a canonical BookForge book through receipt-backed stages.
- This is the bridge Nanda needs between ideation chat and real book workspace creation.

Lifecycle
- `draft`: provisional `BookIntent` under `workspace/book_intents/<intent_id>/book_intent.json`.
- `approved`: authoritative creation source, but no book exists yet.
- `created`: canonical book workspace exists under `workspace/books/<book_id>`.

Commands
- `bookforge book intent list [--status draft|approved|created|shelved] [--json]`
- `bookforge book intent show --intent <intent_id_or_path> [--json]`
- `bookforge book intent draft --title <title> --author-ref <slug/vN> --genre <csv> --seed-text <text> [--book-id <id>] [--json]`
- `bookforge book intent draft --title <title> --author-ref <slug/vN> --genre <csv> --seed-file <path> [--json]`
- `bookforge book intent approve --intent <intent_id_or_path> [--json]`
- `bookforge book intent create --intent <intent_id_or_path> [--book-id <id>] [--series-id <id>] [--json]`
- After create: `bookforge workflow draft-starter-outline --book <book_id> [--chapters N] [--sections-per-chapter N] [--scenes-per-section N] [--json]`

Python Surfaces
- `bookforge.query.list_book_intents(workspace)`
- `bookforge.query.get_book_intent(workspace, intent_ref)`
- `bookforge.execution.build_draft_book_intent_request(...)`
- `bookforge.execution.draft_book_intent_action(workspace, request)`
- `bookforge.execution.build_approve_book_intent_request(...)`
- `bookforge.execution.approve_book_intent_action(workspace, request)`
- `bookforge.execution.build_create_book_from_intent_request(...)`
- `bookforge.execution.create_book_from_intent_action(workspace, request)`
- `bookforge.execution.build_draft_starter_outline_request(...)`
- `bookforge.execution.draft_starter_outline_from_intent(workspace, request)`

Truth Rules
- Drafted intents are provisional and useful for review, not canonical book state.
- Approved intents are authoritative inputs for book creation.
- `create_book_from_intent` is the canonical transition from author-only seed to book scope.
- `draft_starter_outline_from_intent` is the next narrow transition from book scope to workflow-ready outline source artifacts.
- Starter/thin outline drafting uses the configured outline provider, but it does not run the full deep-outline pipeline, initialize workflow state, freeze a section, create a branch, or write prose.
- A created book receives:
  - `book.json` with `book_intent_id`, `book_intent_ref`, and selected intent fields
  - `book_intent.json`
  - `draft/context/book_intent.md`
  - `draft/context/bible.md` seeded from the intent when empty
  - regenerated `prompts/system_v1.md`

Nanda Consumption Notes
- Use `book intent draft` after author-only chat has enough title, author, genre, and seed detail.
- Show `approve` as an approval-gated transition.
- Show `create` as canonical mutation; only after its receipt should Nanda switch from author-only chat to book-scoped authoring.
- After `create`, show `workflow draft-starter-outline` as the provider-backed starter outline action that makes the book eligible for `initialize_section_workflow`.
- The expected sequence for a new book smoke is: draft intent -> approve intent -> create book -> draft starter outline -> initialize workflow -> freeze first section -> create branch -> continue scene.
- Use `workflow legal-actions --book __book_intents__ --workflow-family book_intent --json` for dynamic action availability.
