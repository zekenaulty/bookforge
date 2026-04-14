from __future__ import annotations

import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def test_generated_skilltree_contains_required_files() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    manifest_path = repo_root / "skills" / "bookforge" / "skilltree.manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = {"README.md", "AGENT.md", "SKILL.md", "CLAUDE.md", "HELP.md", "skill.py"}

    for item in payload["skills"]:
        skill_dir = repo_root / "skills" / "bookforge" / item["folder"]
        assert skill_dir.exists(), f"Missing skill directory: {skill_dir}"
        names = {path.name for path in skill_dir.iterdir() if path.is_file()}
        missing = required - names
        assert not missing, f"{skill_dir} is missing files: {sorted(missing)}"


def test_generated_skill_module_can_be_loaded_by_path() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    skill_path = repo_root / "skills" / "bookforge" / "outline" / "chapter-spine" / "skill.py"
    spec = spec_from_file_location("bookforge_skill_module", skill_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.run(module.SKILL.example_params, dry_run=True)
    assert result["skill"]["skill_id"] == "bookforge.outline.chapter-spine"
