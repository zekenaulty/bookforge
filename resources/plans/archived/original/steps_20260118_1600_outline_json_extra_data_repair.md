# Step Notes: Outline JSON Extra-Data Repair

Goal
- Recover outline JSON when the model prematurely closes the chapters array or top-level object, leaving extra data.

Context
- Gemini output occasionally closes the chapters array or the root object early, causing JSONDecodeError: Extra data.
- The failure often appears at a chapter boundary or right before top-level threads/characters.

Files
- src/bookforge/outline.py

Decision
- Add repair logic that reopens the chapters array or top-level object when extra data continues with more chapters or top-level keys.
- Apply repair iteratively to handle multiple premature closures in a single response.

Completion
- Added matching-bracket scan to locate the chapters array end.
- Added repair for early closure before additional chapters or top-level threads/characters.
- Repair loop applies multiple passes before appending missing closers.

Next Actions
- Re-run outline generation and confirm it succeeds on previous failing logs.
