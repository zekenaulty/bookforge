# Book Workflow Orchestrator

Use this skill when a request maps to `book_workflow`.

Required params
- `workspace`
- `book_id`
- `request`

Optional params
- `chapter`
- `section`
- `scene`
- `notes`

Output
- a concise routing plan with required inputs and refusal reasons if prerequisites are missing
