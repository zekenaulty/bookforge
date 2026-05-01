# Slice Note: Capability Projection Fixture Sync

Date: 2026-04-29

Repo: BookForge / `ai-book`

Owner: BookForge engine workstream

## Slice

Verify that the static BookForge capability projection fixture Nanda consumes is current while Nanda works on `/api/scope-capabilities`.

## Result

The live projection and Nanda fixture are currently in sync.

Manual check:

```powershell
$env:PYTHONPATH='src'
@'
import json
from pathlib import Path
from bookforge.query.capabilities import get_capability_projection
live = get_capability_projection().to_dict()
fixture = json.loads(Path("tests/fixtures/capability_projection_v1.json").read_text(encoding="utf-8-sig"))
print("live", len(live["capabilities"]))
print("fixture", len(fixture["capabilities"]))
print("same ids", {c["capability_id"] for c in live["capabilities"]} == {c["capability_id"] for c in fixture["capabilities"]})
print("missing fixture", sorted({c["capability_id"] for c in live["capabilities"]} - {c["capability_id"] for c in fixture["capabilities"]}))
print("stale fixture", sorted({c["capability_id"] for c in fixture["capabilities"]} - {c["capability_id"] for c in live["capabilities"]}))
print("same full", live == fixture)
'@ | python -
```

Output:

```text
live 94
fixture 94
same ids True
missing fixture []
stale fixture []
same full True
```

## Validation

Related test command:

```powershell
python -m pytest tests/test_capability_projection.py -q
```

Included in broader validation:

```text
21 passed in 4.75s
```

from:

```powershell
python -m pytest `
  tests/test_scene_action_execution.py::test_continue_scene_executes_one_recommended_child_and_records_wrapper `
  tests/test_scene_action_execution.py::test_continue_scene_no_ready_child_reports_no_legal_action_stop_reason `
  tests/test_scene_action_execution.py::test_continue_scene_maps_child_outcome_to_loop_stop_reason `
  tests/test_writing_target.py `
  tests/test_capability_projection.py `
  -q
```

## Nanda Reaction Needed

Nanda can safely use `tests/fixtures/capability_projection_v1.json` as the current static projection fixture while building route/scope projection tests.

Important boundary:

- This fixture proves static engine capability truth.
- It does not prove selected route/scope readiness.
- Nanda must still combine it with bridge status, legal actions, readiness, mode policy, approval state, stale state, and UI exposure.

