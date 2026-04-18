from __future__ import annotations

import json
from pathlib import Path

from bookforge.pipeline.chapter_seam import finalize_locked_chapter, seam_report_path


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _outline_payload() -> dict:
    return {
        "chapters": [
            {
                "chapter_id": 1,
                "title": "Test Chapter",
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Setup",
                        "scenes": [
                            {"scene_id": 1},
                            {"scene_id": 2},
                        ],
                    }
                ],
            }
        ]
    }


def test_finalize_locked_chapter_no_op_clean_chapter(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "demo"
    chapter_dir = book_root / "draft" / "chapters" / "ch_001"
    _write_text(
        chapter_dir / "scene_001.md",
        "Artie yanked his arm free at last.\n\nHe stumbled back from the vending machine.",
    )
    _write_text(
        chapter_dir / "scene_002.md",
        "The hallway went quiet around him.\n\nHe checked the machine one more time and walked away.",
    )

    result = finalize_locked_chapter(book_root, _outline_payload(), 1)

    assert result["status"] == "finalized"
    assert result["candidate_path"] is None
    assert result["final_path"] == "draft/chapters/ch_001.md"
    report = json.loads(seam_report_path(book_root, 1).read_text(encoding="utf-8"))
    assert report["after"]["issue_counts"]["error"] == 0


def test_finalize_locked_chapter_repairs_scaffold_and_overlap(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "demo"
    chapter_dir = book_root / "draft" / "chapters" / "ch_001"
    _write_text(
        chapter_dir / "scene_001.md",
        "Artie yanked his arm free at last.\n\nHe stumbled back from the vending machine.",
    )
    _write_text(
        chapter_dir / "scene_002.md",
        "Artie stares at the smoking vending machine, ready to understand what happened.\n\n"
        "The hallway went quiet around him, and he backed toward the breakroom door.",
    )

    result = finalize_locked_chapter(book_root, _outline_payload(), 1)

    assert result["status"] == "finalized"
    assert result["repair_action_count"] >= 1
    final_text = (book_root / "draft" / "chapters" / "ch_001.md").read_text(encoding="utf-8")
    assert "Artie stares at the smoking vending machine" not in final_text
    report = json.loads(seam_report_path(book_root, 1).read_text(encoding="utf-8"))
    assert report["before"]["issue_counts"]["error"] >= 1
    assert report["after"]["issue_counts"]["error"] == 0
