# bookforge visual

Purpose
- Inspect image provider capability, create visual prompt plans, generate provisional image artifacts, and query generated visual assets.
- Visual assets are creative support artifacts. They are not canonical story truth unless a later promotion path defines that explicitly.
- Generation is spend-gated. `visual generate` refuses unless `--allow-spend` is present.

Core flow
- `bookforge visual providers --json`
- `bookforge workflow legal-actions --book <id> --workflow-family visual_assets --json`
- `bookforge visual readiness --book <id> --purpose background_layer --model nano-banana --json`
- `bookforge visual plan --book <id> --prompt-text "<brief>" --json`
- `bookforge visual generate --book <id> --prompt-plan <path> --allow-spend --json`
- `bookforge visual artifacts --book <id> --json`
- `bookforge visual asset --book <id> --asset-id <asset_id> --json`
- `bookforge visual prompt-plan --book <id> --prompt-plan <prompt_plan_id_or_path> --json`

Provider behavior
- Default route: `nano-banana` -> `google:gemini-2.5-flash-image`.
- OpenAI route: `gpt-image-2` / `image-2` -> `openai:gpt-image-2`.
- Both live adapters require credentials:
  - Google: `GEMINI_API_KEY` or `GOOGLE_API_KEY`
  - OpenAI: `OPENAI_API_KEY` or `OPENAI_KEY`
- `gpt-image-2` refuses transparent-background requests because current OpenAI docs say it does not support transparent backgrounds.

Nanda bridge surfaces
- Static capability:
  - `bookforge.query.get_capability_projection(...)`
- Legal action discovery:
  - `bookforge.query.list_execution_options(workspace, ScopeSelector(book_id=<id>, workflow_family="visual_assets"))`
- Readiness:
  - `bookforge.query.get_visual_action_readiness(...)`
- Provider descriptors:
  - `bookforge.query.list_visual_provider_descriptors()`
- Artifact inspection:
  - `bookforge.query.get_visual_asset_index(workspace, book_id, branch_id="main")`
  - `bookforge.query.get_visual_prompt_plan_detail(workspace, book_id, prompt_plan_ref, branch_id="main")`
  - `bookforge.query.get_visual_asset_detail(workspace, book_id, asset_id, branch_id="main")`
- Execution:
  - `bookforge.execution.build_plan_visual_asset_request(...)`
  - `bookforge.execution.plan_visual_asset_action(...)`
  - `bookforge.execution.build_generate_visual_asset_request(...)`
  - `bookforge.execution.generate_visual_asset_action(...)`

Nanda user-facing rule
- Static capability means BookForge knows the action shape.
- Legal action means the action can be considered at the selected scope.
- Readiness means the provider/model/purpose is currently runnable.
- `generate_visual_asset` must show an approval/spend gate before execution.
- Display generated images as provisional artifacts with manifest/receipt evidence.
