# book update-templates

Update prompt templates in one book or all books.
This copies `resources/prompt_templates/*` into each book's `prompts/templates/` folder,
updates `prompts/registry.json`, and rebuilds `prompts/system_v1.md` using the
current book.json and author fragment.

Usage
- Update all books in the workspace (default):
  bookforge --workspace workspace book update-templates

- Update a single book by id:
  bookforge --workspace workspace book update-templates --book starwrought_b1_v1

Notes
- This overwrites per-book prompt templates with the latest versions from resources.
- `system_v1.md` is regenerated after templates are updated.
- If a book's author fragment is missing, the command fails.
