# bookforge init

Purpose
- Create a new book workspace with book.json, state.json, and prompt scaffolding.

Usage
- bookforge init --book <id> --author-ref <author_slug>/vN --title "<title>" --genre "<genre_list>" [--target <key=value>]... [--series-id <series_id>]

Scope
- Requires explicit book id.

Required parameters
- --book: Book id slug.
- --author-ref: Author reference, e.g. eldrik-vale/v3.
- --title: Book title.
- --genre: Comma-separated genre list.

Optional parameters
- --target: Repeatable key=value target (e.g. chapters=24).
- --series-id: Optional series identifier (defaults to the book id when omitted).
- --workspace: Override workspace root (global option).

Outputs
- Creates workspace/books/<BOOK_ID>/ with book.json, state.json, prompts/, outline/, canon/, draft/, exports/, logs/.
- Creates workspace/series/<SERIES_ID>/ with series.json and canon/ scaffolding.
- Writes prompts/system_v1.md assembled from base rules, book constitution, and author fragment.

Examples
- Minimal:
  bookforge init --book my_novel_v1 --author-ref eldrik-vale/v3 --title "Untitled" --genre "fantasy"
- With optional parameters:
  bookforge --workspace workspace init --book my_novel_v1 --author-ref eldrik-vale/v3 --title "Untitled" --genre "fantasy,epic" --target chapters=24 --target avg_scene_words=1900 --series-id "sagefall"
