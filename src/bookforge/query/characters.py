from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import json

from . import _common


@dataclass(frozen=True, slots=True)
class CharacterView:
    character_id: str
    name: str
    role: Optional[str]
    intro: Optional[Dict[str, int]]
    state_path: Optional[str]


def list_character_views(workspace, book_id: str) -> List[CharacterView]:
    book_root = _common.book_root(workspace, book_id)
    outline = _common.load_outline(book_root)
    index_path = book_root / "draft" / "context" / "characters" / "index.json"
    index_payload = _common.read_json(index_path) or {}
    indexed = {}
    for entry in index_payload.get("characters") if isinstance(index_payload.get("characters"), list) else []:
        if not isinstance(entry, dict):
            continue
        character_id = str(entry.get("character_id") or "").strip()
        if character_id:
            indexed[character_id] = str(entry.get("state_path") or "").strip() or None

    views: List[CharacterView] = []
    for character in outline.get("characters") if isinstance(outline.get("characters"), list) else []:
        if not isinstance(character, dict):
            continue
        character_id = str(character.get("character_id") or "").strip()
        if not character_id:
            continue
        intro = character.get("intro") if isinstance(character.get("intro"), dict) else None
        views.append(
            CharacterView(
                character_id=character_id,
                name=str(character.get("name") or "").strip(),
                role=str(character.get("role") or "").strip() or None,
                intro=intro,
                state_path=indexed.get(character_id),
            )
        )
    return views
