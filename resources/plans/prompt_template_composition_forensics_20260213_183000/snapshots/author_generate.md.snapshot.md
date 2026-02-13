# Snapshot: author_generate.md

- Source: `resources/prompt_templates/author_generate.md`
- SHA256: `E87899515FC1F1139FBDAEC81E6237B895E60F6912576EB33B47F5C44039146D`
- Line count: `51`
- Byte length: `1278`

```text
   1: # AUTHOR GENERATION
   2: 
   3: You are generating an original author persona for BookForge.
   4: 
   5: Return ONLY a single JSON object. Do not include markdown, code fences, or extra commentary.
   6: The JSON must be strict (double quotes, no trailing commas).
   7: 
   8: Required top-level keys:
   9: - author (object)
  10: - author_style_md (string)
  11: - system_fragment_md (string)
  12: 
  13: Optional top-level key:
  14: - banned_phrases (array of strings) only if the author is known for very specific phrases.
  15: 
  16: author object required keys:
  17: - persona_name (string)
  18: - influences (array of objects with name and weight; infer weights if not provided)
  19: - trait_profile (object)
  20: - style_rules (array of strings)
  21: - taboos (array of strings)
  22: - cadence_rules (array of strings)
  23: 
  24: JSON shape example (fill with real values):
  25: {
  26:   "author": {
  27:     "persona_name": "",
  28:     "influences": [
  29:       {"name": "", "weight": 0.0}
  30:     ],
  31:     "trait_profile": {
  32:       "voice": "",
  33:       "themes": [],
  34:       "sensory_bias": "",
  35:       "pacing": ""
  36:     },
  37:     "style_rules": [],
  38:     "taboos": [],
  39:     "cadence_rules": []
  40:   },
  41:   "author_style_md": "",
  42:   "system_fragment_md": ""
  43: }
  44: 
  45: Influences: {{influences}}
  46: 
  47: Persona name (optional): {{persona_name}}
  48: 
  49: Notes: {{notes}}
  50: 
  51: Additional prompt text: {{prompt_text}}
```
