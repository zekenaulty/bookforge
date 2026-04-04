# llm

LLM utilities for inspecting thought signatures and requesting a structured "current thoughts" summary.

## Commands

### `bookforge llm signatures`
List recorded thought signatures.

Examples:
```bash
bookforge llm signatures --limit 50
bookforge llm signatures --phase phase_04a_transition_seam_analysis --chapter 6
```

### `bookforge llm current-thoughts`
Ask the model to summarize its current context without chain-of-thought. Optionally use a prior signature for continuity.

Examples:
```bash
bookforge llm current-thoughts --model-phase planner
bookforge llm current-thoughts --signature-id <id> --model-phase planner --thinking-level low
bookforge llm current-thoughts --global-author --model-phase planner
```

### `bookforge llm active`
Show the active thought signature pointer file.

Examples:
```bash
bookforge llm active
```

### `bookforge llm set-active`
Set the active thought signature pointer using a selected signature.

Examples:
```bash
bookforge llm set-active --signature-id <id>
bookforge llm set-active --phase phase_04a_transition_seam_analysis --chapter 6
bookforge llm set-active --global-author --outcome
```

## Notes
- Thought signatures are stored as opaque blobs. They are never decoded or exposed as chain-of-thought.
- The active pointer is a convenience view; the ledger is the source of truth.

### Active pointer policy
The active pointer prefers T1 (intent) by default and records T2 as outcome when available.

You can tune the policy via env vars:
```
THOUGHT_ACTIVE_POLICY_DEFAULT=prefer_t1_with_outcome
THOUGHT_ACTIVE_POLICY_PHASE_04A_TRANSITION_SEAM_ANALYSIS=prefer_t1
THOUGHT_ACTIVE_POLICY_PHASE_04B_TRANSITION_EXECUTION=prefer_t1
```

Supported values:
- `prefer_t1`
- `prefer_t1_with_outcome`
- `prefer_t2`
- `prefer_latest`

### Perspective replay (opt-in)
To inject a perspective block into prompts, set one of:
```
BOOKFORGE_PERSPECTIVE_TEXT="...inline text..."
BOOKFORGE_PERSPECTIVE_PATH=workspace/logs/llm/current_thoughts_latest.json
BOOKFORGE_PERSPECTIVE_MODE=prefix
```

If `BOOKFORGE_PERSPECTIVE_MODE=prefix`, the block is prefixed to prompts. If unset, it defaults to `prefix` when a perspective source is provided.
