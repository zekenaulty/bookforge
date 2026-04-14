from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "skills" / "bookforge"
MANIFEST_PATH = SKILLS_ROOT / "skilltree.manifest.json"
REQUIRED_FILES = ("README.md", "AGENT.md", "SKILL.md", "CLAUDE.md", "HELP.md", "skill.py")


def _read_manifest() -> Dict[str, Any]:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manifest root must be an object.")
    return payload


def _bullet_lines(values: Iterable[str]) -> str:
    items = [str(value) for value in values]
    return "\n".join(f"- `{value}`" for value in items) or "- none"


def _json_literal(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, indent=2)


def _readme_content(item: Dict[str, Any]) -> str:
    return f"""# {item["display_name"]}

Skill id: `{item["skill_id"]}`
Kind: `{item["kind"]}`
Graph node: `{item["graph_node"]}`
Phase id: `{item["phase_id"]}`
Logical phase: `{item["logical_phase"]}`

## Purpose
- {item["llm_description"]}

## Prompt Contract
- {item["prompt_contract"]}

## References
{_bullet_lines(item.get("source_refs", []))}
"""


def _agent_content(item: Dict[str, Any]) -> str:
    return f"""# {item["display_name"]}

Use this skill when a request maps to `{item["graph_node"]}`.

Required params
{_bullet_lines(item.get("required_params", []))}

Optional params
{_bullet_lines(item.get("optional_params", []))}

Output
- {item["output_hint"]}
"""


def _skill_content(item: Dict[str, Any]) -> str:
    name = str(item["folder"]).split("/")[-1]
    return f"""---
name: {name}
description: {item["llm_description"]}
metadata:
  skill_id: {item["skill_id"]}
  display_name: {item["display_name"]}
  kind: {item["kind"]}
  graph_node: {item["graph_node"]}
  phase_id: {item["phase_id"]}
  logical_phase: {item["logical_phase"]}
---

# {item["display_name"]}

Use this skill when the task belongs to `{item["graph_node"]}` in the BookForge skill tree.

Prompt contract
- {item["prompt_contract"]}

Output
- {item["output_hint"]}
"""


def _claude_content(item: Dict[str, Any]) -> str:
    return f"""# {item["display_name"]}

Stay aligned with BookForge source-of-truth files before improvising.
Prefer passed params over guessed workspace context.
Do not invent missing schema fields or state transitions.
Return {item["output_hint"]}.
"""


def _help_content(item: Dict[str, Any]) -> str:
    folder = item["folder"]
    return f"""# {item["display_name"]} Help

## CLI
```bash
python skills/bookforge/{folder}/skill.py --dump-example > params.json
python skills/bookforge/{folder}/skill.py --dry-run --params-file params.json
python skills/bookforge/{folder}/skill.py --params-file params.json
```

## Python
```python
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

path = Path("skills/bookforge/{folder}/skill.py")
spec = spec_from_file_location("bookforge_skill", path)
module = module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

result = module.run(module.SKILL.example_params, dry_run=True)
print(result["user_prompt"])
```
"""


def _skill_py_content(item: Dict[str, Any]) -> str:
    metadata = dict(item)
    return f"""from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[4]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from bookforge.skill_runtime import build_skill_definition, execute_skill, skill_main


SKILL = build_skill_definition({ _json_literal(metadata) })


def run(params: Dict[str, Any], *, dry_run: bool = False, **kwargs: Any) -> Dict[str, Any]:
    return execute_skill(SKILL, params, dry_run=dry_run, **kwargs)


if __name__ == "__main__":
    raise SystemExit(skill_main(SKILL))
"""


def _root_readme(manifest: Dict[str, Any]) -> str:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for item in manifest.get("skills", []):
        groups.setdefault(str(item["category"]), []).append(item)

    lines = [
        "# BookForge Skill Tree",
        "",
        f"Schema version: `{manifest['schema_version']}`",
        "",
        "This tree is generated from `skills/bookforge/skilltree.manifest.json`.",
        "",
    ]
    for category in ("orchestrators", "outline", "run"):
        items = groups.get(category, [])
        if not items:
            continue
        lines.append(f"## {category.title()}")
        for item in items:
            lines.append(
                f"- `{item['skill_id']}` -> `skills/bookforge/{item['folder']}` "
                f"({item['graph_node']} / {item['phase_id']})"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _write_skill(item: Dict[str, Any]) -> None:
    target = SKILLS_ROOT / str(item["folder"])
    target.mkdir(parents=True, exist_ok=True)
    files = {
        "README.md": _readme_content(item),
        "AGENT.md": _agent_content(item),
        "SKILL.md": _skill_content(item),
        "CLAUDE.md": _claude_content(item),
        "HELP.md": _help_content(item),
        "skill.py": _skill_py_content(item),
    }
    for name, content in files.items():
        (target / name).write_text(content.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    manifest = _read_manifest()
    SKILLS_ROOT.mkdir(parents=True, exist_ok=True)
    (SKILLS_ROOT / "README.md").write_text(_root_readme(manifest), encoding="utf-8")
    for item in manifest.get("skills", []):
        _write_skill(item)

    expected = len(manifest.get("skills", []))
    print(f"Generated {expected} skill folders at {SKILLS_ROOT}")
    print(f"Required files per skill: {', '.join(REQUIRED_FILES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
