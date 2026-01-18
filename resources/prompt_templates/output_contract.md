Output must follow the requested format.
JSON blocks must be valid and schema-compliant.
All required keys and arrays must be present.
When a prompt specifies required counts or ranges, treat them as hard constraints.
Do not collapse arrays below the stated minimums.
If multiple output blocks are required (e.g. PROSE and STATE_PATCH), include all blocks in order.
If output must be JSON only, return a single JSON object with no commentary or code fences.
When creating outlines, the total scenes per chapter (sum of sections[].scenes[]) must match chapters[].pacing.expected_scene_count.