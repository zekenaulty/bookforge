from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from bookforge.execution.author_assets import (
    AUTHOR_LIBRARY_SCOPE_ID,
    build_create_author_request,
    build_refine_author_request,
    create_author_action,
    refine_author_action,
)
from bookforge.query import list_execution_options
from bookforge.contracts import ScopeSelector


def _write_author_version(workspace: Path, *, name: str, notes: str = "") -> Path:
    slug = name.strip().lower().replace(" ", "-")
    author_root = workspace / "authors" / slug
    index_path = author_root / "index.json"
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        versions = list(index.get("versions") or [])
    else:
        versions = []
    version = f"v{len(versions) + 1}"
    version_dir = author_root / version
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / "author.json").write_text(
        json.dumps(
            {
                "persona_name": name,
                "trait_profile": {
                    "voice": "Precise and humane.",
                    "themes": ["earned competence"],
                    "sensory_bias": "metal, rain, warm paper",
                    "pacing": "measured pressure",
                },
                "style_rules": ["Make causal stakes visible."],
                "taboos": ["empty spectacle"],
                "cadence_rules": ["Short pressure beats after long setup."],
                "influences": [{"name": "fixture", "weight": 1}],
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    (version_dir / "author_style.md").write_text("A measured, pressure-forward voice.", encoding="utf-8")
    (version_dir / "system_fragment.md").write_text("Write with precise, humane pressure.", encoding="utf-8")
    versions.append(
        {
            "version": version,
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "notes": notes,
            "files": {
                "author_json": f"{version}/author.json",
                "author_style_md": f"{version}/author_style.md",
                "system_fragment_md": f"{version}/system_fragment.md",
            },
        }
    )
    index_path.write_text(
        json.dumps(
            {
                "author_slug": slug,
                "display_name": name,
                "default_version": version,
                "versions": versions,
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    return version_dir


def test_author_asset_actions_are_discoverable() -> None:
    selector = ScopeSelector(book_id=AUTHOR_LIBRARY_SCOPE_ID, workflow_family="author_assets")
    options = {option.action: option for option in list_execution_options(Path("workspace"), selector)}

    assert options["create_author"].allowed is True
    assert options["refine_author"].allowed is True
    assert options["create_author"].workflow_family == "author_assets"
    assert "details.author_ref" in options["refine_author"].selector_requirements


def test_create_author_action_emits_authoritative_receipt(tmp_path: Path, monkeypatch) -> None:
    def fake_generate_author(*, workspace, influences, prompt_file, name, notes, prompt_text=None):
        assert influences == "fixture"
        assert prompt_file is None
        assert prompt_text is None
        return _write_author_version(Path(workspace), name=name or "Fixture Author", notes=notes or "")

    monkeypatch.setattr("bookforge.execution.author_assets.generate_author", fake_generate_author)
    request = build_create_author_request(name="Fixture Author", influences="fixture", notes="created by test")

    result = create_author_action(tmp_path, request)

    assert result.status == "success"
    assert result.action == "create_author"
    assert result.node.workflow_family == "author_assets"
    assert result.selector.book_id == AUTHOR_LIBRARY_SCOPE_ID
    assert result.details["author_ref"] == "fixture-author/v1"
    assert {artifact.artifact_status for artifact in result.produced_artifacts} == {"authoritative"}
    assert (tmp_path / "authors" / "fixture-author" / "v1" / "author.json").exists()


def test_refine_author_action_creates_successor_version(tmp_path: Path, monkeypatch) -> None:
    _write_author_version(tmp_path, name="Fixture Author", notes="base")

    def fake_generate_author(*, workspace, influences, prompt_file, name, notes, prompt_text=None):
        assert influences is None
        assert prompt_file is None
        assert "Requested refinement" in str(prompt_text)
        return _write_author_version(Path(workspace), name=name or "Fixture Author", notes=notes or "")

    monkeypatch.setattr("bookforge.execution.author_assets.generate_author", fake_generate_author)
    request = build_refine_author_request(
        author_ref="fixture-author/v1",
        instructions="Make the voice warmer without losing precision.",
        notes="warmer refinement",
    )

    result = refine_author_action(tmp_path, request)

    assert result.status == "success"
    assert result.action == "refine_author"
    assert result.details["author_ref"] == "fixture-author/v2"
    assert result.details["source_author_ref"] == "fixture-author/v1"
    assert (tmp_path / "authors" / "fixture-author" / "v1" / "author.json").exists()
    assert (tmp_path / "authors" / "fixture-author" / "v2" / "author.json").exists()

