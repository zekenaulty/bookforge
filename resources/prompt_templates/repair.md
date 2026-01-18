# REPAIR

Fix the scene based on lint issues.
Return corrected prose plus a corrected state_patch JSON block.

Output format (required, no code fences, no commentary):
PROSE:
<scene prose>

STATE_PATCH:
<json>

Rules:
- STATE_PATCH must be a single JSON object with double quotes and no trailing commas.

Issues:
{{issues}}

Scene:
{{prose}}

State:
{{state}}
