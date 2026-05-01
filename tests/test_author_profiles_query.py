from __future__ import annotations

import json
from pathlib import Path

from bookforge.cli import build_parser
from bookforge.query.authors import get_author_profile, list_author_profiles


def _write_author(root: Path) -> None:
    author_root = root / "authors" / "eldrik-vale"
    version_root = author_root / "v2"
    version_root.mkdir(parents=True)
    (author_root / "index.json").write_text(
        json.dumps(
            {
                "author_slug": "eldrik-vale",
                "display_name": "Eldrik Vale",
                "default_version": "v2",
                "versions": [
                    {
                        "version": "v2",
                        "created_at": "2026-02-12T00:00:00Z",
                        "notes": "LitRPG author with mechanical clarity and slow-burn dread.",
                        "files": {
                            "author_json": "v2/author.json",
                            "author_style_md": "v2/author_style.md",
                            "system_fragment_md": "v2/system_fragment.md",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (version_root / "author.json").write_text(
        json.dumps(
            {
                "persona_name": "Eldrik Vale",
                "trait_profile": {
                    "voice": "Sharp, funny, mechanically exact.",
                    "themes": ["optimization as survival", "found family through shared trauma"],
                    "sensory_bias": "Tactile and auditory system detail.",
                    "pacing": "Fast action with strategic breathers.",
                },
                "style_rules": ["Respect the stat sheet."],
                "taboos": ["No vague magic."],
                "cadence_rules": ["Short sentences during combat."],
                "banned_phrases": ["a surge of power"],
                "influences": [{"name": "Will Wight", "weight": 0.8}],
            }
        ),
        encoding="utf-8",
    )
    (version_root / "author_style.md").write_text(
        "Eldrik writes progression fantasy like a systems engineer telling a war story.",
        encoding="utf-8",
    )
    (version_root / "system_fragment.md").write_text(
        "You are Eldrik Vale. Use sharp mechanics, tight POV, and earned progression.",
        encoding="utf-8",
    )


def test_author_profile_query_exposes_rich_voice_surface(tmp_path: Path) -> None:
    _write_author(tmp_path)

    profiles = list_author_profiles(tmp_path)
    profile = get_author_profile(tmp_path, "eldrik-vale")
    payload = profile.to_dict()

    assert len(profiles) == 1
    assert payload["author_ref"] == "eldrik-vale/v2"
    assert payload["artifact_status"] == "authoritative"
    assert payload["voice"] == "Sharp, funny, mechanically exact."
    assert payload["themes"] == ["optimization as survival", "found family through shared trauma"]
    assert "systems engineer" in payload["short_description"]
    assert "## Soul And Style" in payload["profile_markdown"]
    assert "## System Fragment" in payload["profile_markdown"]
    assert payload["source_paths"]["author_json"] == "eldrik-vale/v2/author.json"


def test_author_profile_cli_commands_parse() -> None:
    parser = build_parser()

    author_list = parser.parse_args(["author", "list", "--json"])
    author_profile = parser.parse_args(["author", "profile", "eldrik-vale/v2", "--json"])

    assert author_list.author_command == "list"
    assert author_profile.author_command == "profile"
    assert author_profile.author_ref == "eldrik-vale/v2"
