import json
import pytest

from bookforge.prompt.registry import load_registry


def test_load_registry(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text(
        json.dumps({"version": "v1", "templates": {"plan": "plan.md"}}),
        encoding="utf-8",
    )
    registry = load_registry(path)
    assert registry.version == "v1"
    assert registry.templates["plan"] == "plan.md"


def test_load_registry_missing_version(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps({"templates": {"plan": "plan.md"}}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_registry(path)
