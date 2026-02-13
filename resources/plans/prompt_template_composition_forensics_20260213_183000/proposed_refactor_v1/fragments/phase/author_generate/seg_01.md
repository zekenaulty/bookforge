# AUTHOR GENERATION

You are generating an original author persona for BookForge.

Return ONLY a single JSON object. Do not include markdown, code fences, or extra commentary.
The JSON must be strict (double quotes, no trailing commas).

Required top-level keys:
- author (object)
- author_style_md (string)
- system_fragment_md (string)

Optional top-level key:
- banned_phrases (array of strings) only if the author is known for very specific phrases.

author object required keys:
- persona_name (string)
- influences (array of objects with name and weight; infer weights if not provided)
- trait_profile (object)
- style_rules (array of strings)
- taboos (array of strings)
- cadence_rules (array of strings)

JSON shape example (fill with real values):
{
  "author": {
    "persona_name": "",
    "influences": [
      {"name": "", "weight": 0.0}
    ],
    "trait_profile": {
      "voice": "",
      "themes": [],
      "sensory_bias": "",
      "pacing": ""
    },
    "style_rules": [],
    "taboos": [],
    "cadence_rules": []
  },
  "author_style_md": "",
  "system_fragment_md": ""
}

Influences: {{influences}}

Persona name (optional): {{persona_name}}

Notes: {{notes}}

Additional prompt text: {{prompt_text}}

