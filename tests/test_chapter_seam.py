from __future__ import annotations

import json
from pathlib import Path

from bookforge.pipeline.chapter_seam import finalize_locked_chapter, seam_report_path


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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


def test_finalize_locked_chapter_writes_original_fixed_and_final_versions(tmp_path: Path, monkeypatch) -> None:
    book_root = tmp_path / "books" / "demo"
    chapter_dir = book_root / "draft" / "chapters" / "ch_001"
    scene_1 = "Artie yanked his arm free at last.\n\nHe stumbled back from the vending machine."
    scene_2 = "The hallway went quiet around him.\n\nHe checked the machine one more time and walked away."
    _write_text(chapter_dir / "scene_001.md", scene_1)
    _write_text(chapter_dir / "scene_002.md", scene_2)

    def _noop_pairs(book_root_arg: Path, outline_arg: dict, chapter_num: int, blocks: list[dict]) -> tuple[list[dict], list[dict]]:
        return [dict(block) for block in blocks], []

    monkeypatch.setattr("bookforge.pipeline.chapter_seam._run_chapter_seam_pairs", _noop_pairs)

    result = finalize_locked_chapter(book_root, _outline_payload(), 1)

    assert result["status"] == "finalized"
    assert result["original_path"] == "draft/chapters/ch_001.original.md"
    assert result["fixed_path"] == "draft/chapters/ch_001.fixed.md"
    assert result["final_path"] == "draft/chapters/ch_001.md"
    assert result["candidate_path"] is None

    assert _read_text(chapter_dir / "scene_001.original.md").strip() == scene_1
    assert _read_text(chapter_dir / "scene_001.fixed.md").strip() == scene_1
    assert _read_text(chapter_dir / "scene_001.md").strip() == scene_1
    assert _read_text(book_root / "draft" / "chapters" / "ch_001.original.md").startswith("# Chapter 1")
    assert _read_text(book_root / "draft" / "chapters" / "ch_001.fixed.md").startswith("# Chapter 1")
    report = json.loads(seam_report_path(book_root, 1).read_text(encoding="utf-8"))
    assert report["after"]["issue_counts"]["error"] == 0


def test_finalize_locked_chapter_promotes_repaired_scene_versions(tmp_path: Path, monkeypatch) -> None:
    book_root = tmp_path / "books" / "demo"
    chapter_dir = book_root / "draft" / "chapters" / "ch_001"
    scene_1 = (
        "[Acknowledge indenture status to commence mandatory labor cycle. Y / N]\n"
        "[Warning: Selecting 'N' or failing to acknowledge within the grace period will result in immediate asset liquidation. (Current Asset Value: 1 HP).]\n\n"
        "Rhea stared at the prompt. The claustrophobia was absolute. She was physically pinned under hundreds of pounds of obsidian, "
        "held together by a single hit point. But far worse, she was legally pinned by a terms of service agreement that held a gun to her head."
    )
    scene_2_original = (
        "Rhea gritted her teeth, her lungs fighting for air beneath the jagged obsidian debris that kept her pinned to the scorched earth. "
        "She couldn't even assess the damage to her trapped left leg, because a glowing blue notification hung exactly two inches from her nose, "
        "keeping her vision entirely blocked.\n\n"
        "[Indenture Status: Pending Registration]\n"
        "[Soul Debt Assessed: 100,000 Credits]\n"
        "[Acknowledge terms to receive Standard Frontier Starter Pack and immediate Medical Relief.]\n"
        "[Accept] | [Accept (Expedited)]"
    )
    scene_2_fixed = (
        "Her next breath snagged under the obsidian load before she forced herself to focus past the ache in her leg.\n\n"
        "[Indenture Status: Pending Registration]\n"
        "[Soul Debt Assessed: 100,000 Credits]\n"
        "[Acknowledge terms to receive Standard Frontier Starter Pack and immediate Medical Relief.]\n"
        "[Accept] | [Accept (Expedited)]"
    )
    _write_text(chapter_dir / "scene_001.md", scene_1)
    _write_text(chapter_dir / "scene_002.md", scene_2_original)

    def _repair_pairs(book_root_arg: Path, outline_arg: dict, chapter_num: int, blocks: list[dict]) -> tuple[list[dict], list[dict]]:
        repaired = [dict(block) for block in blocks]
        repaired[1]["text"] = scene_2_fixed
        return repaired, [
            {
                "pair_index": 1,
                "from_scene_ref": "1:1",
                "to_scene_ref": "1:2",
                "status": "pass",
                "repair_applied": True,
                "passes_used": 1,
                "issues_before": [{"code": "restart_energy_overlap", "message": "overlap"}],
                "issues_after": [],
                "pass_records": [
                    {
                        "pass": 1,
                        "lint": {"schema_version": "1.0", "status": "fail", "issues": [{"code": "restart_energy_overlap", "message": "overlap"}]},
                        "repair": {
                            "status": "repaired",
                            "changed": True,
                            "scene_a_tail_preview": "",
                            "scene_b_head_preview": "Her next breath snagged under the obsidian load before she forced herself to focus past the ache in her leg.",
                            "notes": ["Removed restart energy at the boundary."],
                        },
                    }
                ],
            }
        ]

    monkeypatch.setattr("bookforge.pipeline.chapter_seam._run_chapter_seam_pairs", _repair_pairs)

    result = finalize_locked_chapter(book_root, _outline_payload(), 1)

    assert result["status"] == "finalized"
    assert result["repair_action_count"] == 1
    assert _read_text(chapter_dir / "scene_002.original.md").strip() == scene_2_original
    assert _read_text(chapter_dir / "scene_002.fixed.md").strip() == scene_2_fixed
    assert _read_text(chapter_dir / "scene_002.md").strip() == scene_2_fixed
    assert "Her next breath snagged under the obsidian load" in _read_text(book_root / "draft" / "chapters" / "ch_001.md")
    report = json.loads(seam_report_path(book_root, 1).read_text(encoding="utf-8"))
    assert report["status"] == "finalized"
    assert report["repair_action_count"] == 1
    assert report["pairs"][0]["repair_applied"] is True


def test_finalize_locked_chapter_keeps_canonical_scene_when_post_seam_audit_fails(tmp_path: Path, monkeypatch) -> None:
    book_root = tmp_path / "books" / "demo"
    chapter_dir = book_root / "draft" / "chapters" / "ch_001"
    scene_1 = "The heavy blast door slid open, revealing the dark corridor beyond."
    scene_2 = (
        "The heavy blast doors hissed open into the polished stone corridor, immediately triggering a barrage of automated bolts.\n\n"
        "[Formal Dispute Status: Active. System Review Initiated.]\n\n"
        "The bloated avatar of administrative code roared and launched itself over the desk."
    )
    _write_text(chapter_dir / "scene_001.md", scene_1)
    _write_text(chapter_dir / "scene_002.md", scene_2)

    def _failing_pairs(book_root_arg: Path, outline_arg: dict, chapter_num: int, blocks: list[dict]) -> tuple[list[dict], list[dict]]:
        return [dict(block) for block in blocks], [
            {
                "pair_index": 1,
                "from_scene_ref": "1:1",
                "to_scene_ref": "1:2",
                "status": "attention_required",
                "repair_applied": False,
                "passes_used": 1,
                "issues_before": [{"code": "overlap_lead_sentence", "message": "overlap"}],
                "issues_after": [{"code": "overlap_lead_sentence", "message": "overlap"}],
                "pass_records": [
                    {
                        "pass": 1,
                        "lint": {"schema_version": "1.0", "status": "fail", "issues": [{"code": "overlap_lead_sentence", "message": "overlap"}]},
                    }
                ],
            }
        ]

    monkeypatch.setattr("bookforge.pipeline.chapter_seam._run_chapter_seam_pairs", _failing_pairs)

    result = finalize_locked_chapter(book_root, _outline_payload(), 1)

    assert result["status"] == "attention_required"
    assert result["final_path"] is None
    assert result["candidate_path"] == "draft/chapters/ch_001.fixed.md"
    assert _read_text(chapter_dir / "scene_002.original.md").strip() == scene_2
    assert _read_text(chapter_dir / "scene_002.fixed.md").strip() == scene_2
    assert _read_text(chapter_dir / "scene_002.md").strip() == scene_2
    report = json.loads(seam_report_path(book_root, 1).read_text(encoding="utf-8"))
    assert report["status"] == "attention_required"
    assert report["after"]["issue_counts"]["error"] >= 1
