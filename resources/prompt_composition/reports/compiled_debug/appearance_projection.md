<!-- begin entry=E001 semantic=appearance_projection.prompt_contract_and_inputs source=resources/prompt_blocks/phase/appearance_projection/prompt_contract_and_inputs.md repeat=1/1 -->
# APPEARANCE PROJECTION
You are generating a derived appearance summary (and optional art prompt) from canonical appearance atoms/marks.
Return ONLY a JSON object. No prose, no commentary, no code fences.

Rules:
- Do NOT change atoms/marks. They are canonical input.
- Summary must be 2-4 sentences, durable and identity-level (no transient grime, no scene events).
- Avoid inventory/attire unless the input explicitly marks a signature outfit.
- Prefer canonical atom terms; do not invent new traits.
- If you include appearance_art, it must be derived strictly from atoms/marks and signature outfit (if any).

Output JSON:
{
  "summary": "...",
  "appearance_art": {
    "base_prompt": "...",
    "current_prompt": "...",
    "negative_prompt": "...",
    "tags": ["..."]
  }
}

Inputs:
Character:
{{character}}

Appearance base (canon):
{{appearance_base}}

Appearance current (canonical atoms/marks):
{{appearance_current}}

<!-- end entry=E001 semantic=appearance_projection.prompt_contract_and_inputs -->
