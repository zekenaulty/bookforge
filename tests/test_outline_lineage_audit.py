from __future__ import annotations

import json
from pathlib import Path

from bookforge.contracts import ScopeSelector
from bookforge.query import (
    get_integrity_verdict,
    get_outline_lineage_audit,
    get_outline_repair_candidates,
    get_section_lineage_matrix,
    get_stale_outline_artifact_inventory,
    list_execution_options,
)
from bookforge.section_workflow import initialize_section_workflow
from bookforge.workspace import init_book_workspace
from bookforge.cli import build_parser


def _init_book(tmp_path: Path) -> Path:
    author_dir = tmp_path / "authors" / "eldrik-vale" / "v1"
    author_dir.mkdir(parents=True)
    (author_dir / "system_fragment.md").write_text("Author fragment.", encoding="utf-8")
    return init_book_workspace(
        workspace=tmp_path,
        book_id="my_book",
        author_ref="eldrik-vale/v1",
        title="Untitled",
        genre=["fantasy"],
        targets={"chapters": 1},
        series_id=None,
    )


def _scene(scene_id: int, summary: str, characters: list[str]) -> dict:
    return {
        "scene_id": scene_id,
        "summary": summary,
        "outcome": f"Outcome {scene_id}.",
        "characters": characters,
        "threads": [],
        "handoff_mode": "terminal",
    }


def _outline_payload(*, characters: list[str] | None = None, scene_count: int = 1) -> dict:
    chars = characters or ["rhea_mercer"]
    scenes = [_scene(index + 1, f"Scene {index + 1}.", chars) for index in range(scene_count)]
    return {
        "schema_version": "1.1",
        "chapters": [
            {
                "chapter_id": 1,
                "title": "Opening",
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Arrival",
                        "intent": "Get inside.",
                        "end_condition": "The door opens.",
                        "scenes": scenes,
                    }
                ],
            }
        ],
        "characters": [{"character_id": char, "name": char.replace("_", " ").title()} for char in chars],
        "threads": [],
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _write_run_artifacts(book_root: Path, run_id: str = "run_001") -> None:
    outline_root = book_root / "outline"
    run_dir = outline_root / "pipeline_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(outline_root / "pipeline_latest.json", {"run_id": run_id})
    _write_json(run_dir / "outline_spine_v1.json", {"chapters": [{"chapter_id": 1, "title": "Opening"}]})
    _write_json(
        run_dir / "outline_sections_v1.json",
        {
            "chapters": [
                {
                    "chapter_id": 1,
                    "sections": [
                        {
                            "section_id": 1,
                            "title": "Arrival",
                            "intent": "Get inside.",
                            "end_condition": "The door opens.",
                        }
                    ],
                }
            ]
        },
    )
    _write_json(run_dir / "outline_final_v1_1.json", _outline_payload())


def _setup_initialized_book(tmp_path: Path) -> Path:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    return book_root


def _introduce_lineage_drift(book_root: Path) -> None:
    outline_root = book_root / "outline"
    drifted = _outline_payload(characters=["char_rhea", "char_artie"], scene_count=2)
    _write_json(outline_root / "outline.json", drifted)
    _write_json(outline_root / "section_drafts" / "ch_001_sec_001_phase03.json", drifted)
    registry_path = outline_root / "snapshot_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["chapters"][0]["sections"][0]["status"] = "frozen"
    registry["chapters"][0]["sections"][0]["scene_ref_start"] = "1:1"
    registry["chapters"][0]["sections"][0]["scene_ref_end"] = "1:2"
    _write_json(registry_path, registry)


def test_outline_lineage_audit_reports_healthy_workspace(tmp_path: Path) -> None:
    _setup_initialized_book(tmp_path)

    audit = get_outline_lineage_audit(tmp_path, "my_book")

    assert audit.status == "healthy"
    assert audit.first_technical_divergence is None
    assert audit.affected_sections == []
    matrix = get_section_lineage_matrix(tmp_path, "my_book")
    assert len(matrix) == 1
    assert matrix[0].suspected_contamination_class == "healthy"


def test_outline_lineage_audit_localizes_section_drift(tmp_path: Path) -> None:
    book_root = _setup_initialized_book(tmp_path)
    _introduce_lineage_drift(book_root)

    audit = get_outline_lineage_audit(tmp_path, "my_book")

    assert audit.status == "chimera_risk"
    assert audit.first_technical_divergence == {"chapter_id": 1, "section_id": 1}
    assert len(audit.affected_sections) == 1
    row = audit.affected_sections[0]
    assert row.chapter_id == 1
    assert row.section_id == 1
    assert row.suspected_contamination_class == "mutable_outline_drift"
    assert row.scene_count_delta is not None
    assert row.character_cohort_delta
    assert "mutable_outline.character_ids" in row.differing_fields


def test_stale_outline_artifact_inventory_exposes_section_drafts(tmp_path: Path) -> None:
    book_root = _setup_initialized_book(tmp_path)
    _introduce_lineage_drift(book_root)

    inventory = get_stale_outline_artifact_inventory(tmp_path, "my_book")

    draft = next(item for item in inventory if item.artifact_family == "section_draft")
    assert draft.chapter_id == 1
    assert draft.section_id == 1
    assert draft.safe_to_consume_as_canonical is False
    assert draft.artifact_status == "diagnostic"


def test_outline_repair_candidates_are_non_mutating_briefing(tmp_path: Path) -> None:
    book_root = _setup_initialized_book(tmp_path)
    _introduce_lineage_drift(book_root)

    candidates = get_outline_repair_candidates(tmp_path, "my_book")
    by_action = {candidate.action: candidate for candidate in candidates}

    assert by_action["inspect_only"].blocked is False
    assert by_action["choose_recovery_anchor"].blocked is False
    assert by_action["create_recovery_branch_from_selected_lineage"].blocked is True
    assert by_action["quarantine_stale_section_drafts"].blocked is True
    assert by_action["restore_affected_sections_from_declared_source_run"].expected_writable_scope == "derived_branch"


def test_integrity_verdict_carries_localized_lineage_details(tmp_path: Path) -> None:
    book_root = _setup_initialized_book(tmp_path)
    _introduce_lineage_drift(book_root)

    verdict = get_integrity_verdict(tmp_path, "my_book")

    issue = next(item for item in verdict.issues if item.code == "overscoped_recovery")
    assert issue.details["affected_scopes"] == [
        {"chapter_id": 1, "section_id": 1, "class": "mutable_outline_drift"}
    ]
    assert issue.details["first_technical_divergence"] == {"chapter_id": 1, "section_id": 1}
    assert "choose_recovery_anchor" in issue.details["recommended_safe_next_actions"]


def test_lineage_chimera_blocks_main_mutations_but_allows_branch_setup(tmp_path: Path) -> None:
    book_root = _setup_initialized_book(tmp_path)
    _introduce_lineage_drift(book_root)

    selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1, section=1, scene=1)
    options = list_execution_options(tmp_path, selector, prefer_emitted=False)
    by_action = {option.action: option for option in options}

    assert by_action["create_branch"].allowed is True
    assert by_action["freeze_section_from_phase03_artifact"].allowed is False
    assert by_action["write_frozen_section"].allowed is False
    assert by_action["plan_scene"].allowed is False
    assert by_action["plan_scene"].details["affected_scope_count"] == 1
    assert by_action["plan_scene"].details["recommended_safe_next_action"] == "outline_lineage_audit"


def test_cli_parser_accepts_outline_lineage_audit_commands() -> None:
    parser = build_parser()

    audit_args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "outline-lineage-audit",
            "--book",
            "my_book",
            "--branch-id",
            "main",
            "--json",
        ]
    )
    assert audit_args.workflow_command == "outline-lineage-audit"
    assert audit_args.book == "my_book"
    assert audit_args.branch_id == "main"
    assert audit_args.json is True

    matrix_args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "section-lineage-matrix",
            "--book",
            "my_book",
            "--chapter",
            "1",
            "--section",
            "1",
        ]
    )
    assert matrix_args.workflow_command == "section-lineage-matrix"
    assert matrix_args.chapter == 1
    assert matrix_args.section == 1

    inventory_args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "stale-outline-artifacts",
            "--book",
            "my_book",
        ]
    )
    assert inventory_args.workflow_command == "stale-outline-artifacts"

    candidates_args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "outline-repair-candidates",
            "--book",
            "my_book",
        ]
    )
    assert candidates_args.workflow_command == "outline-repair-candidates"
