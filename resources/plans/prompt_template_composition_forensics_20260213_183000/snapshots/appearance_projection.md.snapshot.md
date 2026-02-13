# Snapshot: appearance_projection.md

- Source: `resources/prompt_templates/appearance_projection.md`
- SHA256: `EF863DD5ED891E5B300A56570216752AB98A5E6B6800AE84C302D670FE906E34`
- Line count: `31`
- Byte length: `930`

```text
   1: # APPEARANCE PROJECTION
   2: You are generating a derived appearance summary (and optional art prompt) from canonical appearance atoms/marks.
   3: Return ONLY a JSON object. No prose, no commentary, no code fences.
   4: 
   5: Rules:
   6: - Do NOT change atoms/marks. They are canonical input.
   7: - Summary must be 2-4 sentences, durable and identity-level (no transient grime, no scene events).
   8: - Avoid inventory/attire unless the input explicitly marks a signature outfit.
   9: - Prefer canonical atom terms; do not invent new traits.
  10: - If you include appearance_art, it must be derived strictly from atoms/marks and signature outfit (if any).
  11: 
  12: Output JSON:
  13: {
  14:   "summary": "...",
  15:   "appearance_art": {
  16:     "base_prompt": "...",
  17:     "current_prompt": "...",
  18:     "negative_prompt": "...",
  19:     "tags": ["..."]
  20:   }
  21: }
  22: 
  23: Inputs:
  24: Character:
  25: {{character}}
  26: 
  27: Appearance base (canon):
  28: {{appearance_base}}
  29: 
  30: Appearance current (canonical atoms/marks):
  31: {{appearance_current}}
```
