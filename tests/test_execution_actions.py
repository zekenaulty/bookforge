from __future__ import annotations

import json
from pathlib import Path

from bookforge.execution import (
    build_create_assembly_branch_request,
    build_create_branch_request,
    build_discard_branch_request,
    build_finalize_chapter_request,
    build_freeze_section_request,
    build_initialize_workflow_request,
    build_lock_section_request,
    build_promote_branch_request,
    build_record_assembly_validation_request,
    build_write_section_request,
    create_assembly_branch_action,
    create_branch_action,
    discard_branch_action,
    finalize_chapter,
    freeze_section,
    initialize_workflow,
    lock_section,
    promote_branch_action,
    record_assembly_validation_action,
    write_frozen_section,
)
from bookforge.branching import create_assembly_branch, create_branch, rerun_freeze_section_on_branch
from bookforge.section_workflow import lock_section_from_written_state
from bookforge.supervision import paths as supervision_paths
from bookforge.workspace import init_book_workspace


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


def _write_run_artifacts(book_root: Path, run_id: str = "run_001") -> None:
    outline_root = book_root / "outline"
    run_dir = outline_root / "pipeline_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (outline_root / "pipeline_latest.json").write_text(json.dumps({"run_id": run_id}, ensure_ascii=True, indent=2), encoding="utf-8")
    (run_dir / "outline_spine_v1.json").write_text(
        json.dumps(
            {
                "chapters": [
                    {
                        "chapter_id": 1,
                        "title": "Opening",
                        "goal": "Start the story.",
                        "chapter_role": "hook",
                        "stakes_shift": "Pressure escalates.",
                        "bridge": {"from_prev": "", "to_next": "Move into danger."},
                        "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 1},
                    }
                ]
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_dir / "outline_sections_v1.json").write_text(
        json.dumps(
            {
                "chapters": [
                    {
                        "chapter_id": 1,
                        "sections": [
                            {
                                "section_id": 1,
                                "title": "Arrival",
                                "intent": "Get inside.",
                                "section_role": "setup",
                                "target_scene_count": 1,
                                "end_condition": "The door opens.",
                            }
                        ],
                    }
                ]
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_dir / "outline_final_v1_1.json").write_text(
        json.dumps(
            {
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
                                "scenes": [
                                    {
                                        "scene_id": 1,
                                        "summary": "First scene.",
                                        "handoff_mode": "terminal",
                                        "transition_out_anchors": ["door"],
                                        "threads": [],
                                    }
                                ],
                            }
                        ],
                    }
                ],
                "characters": [{"character_id": "rhea_mercer", "name": "Rhea Mercer", "role": "protagonist"}],
                "threads": [],
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_scene_artifacts(book_root: Path, chapter_id: int, scene_id: int, *, text: str) -> None:
    chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter_id:03d}"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    (chapter_dir / f"scene_{scene_id:03d}.md").write_text(text, encoding="utf-8")
    (chapter_dir / f"scene_{scene_id:03d}.meta.json").write_text(
        json.dumps({"scene_id": scene_id}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def test_initialize_workflow_action_returns_emitted_result(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)

    request = build_initialize_workflow_request(tmp_path, "my_book")
    result = initialize_workflow(tmp_path, request)

    assert result.action == "initialize_section_workflow"
    assert result.status == "success"
    assert result.request_id == request.request_id
    assert result.details["run_id"] == "run_001"
    assert result.artifact_paths["outline"].endswith("outline/outline.json")
    assert result.artifact_paths["registry"].endswith("outline/snapshot_registry.json")


def test_initialize_workflow_action_reports_no_op_after_existing_init(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)

    first_request = build_initialize_workflow_request(tmp_path, "my_book")
    initialize_workflow(tmp_path, first_request)

    second_request = build_initialize_workflow_request(tmp_path, "my_book")
    result = initialize_workflow(tmp_path, second_request)

    assert result.action == "initialize_section_workflow"
    assert result.status == "no_op"
    assert result.request_id == second_request.request_id
    assert result.details["initialized"] is False


def test_freeze_section_action_returns_emitted_result(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    init_request = build_initialize_workflow_request(tmp_path, "my_book")
    initialize_workflow(tmp_path, init_request)

    request = build_freeze_section_request(tmp_path, "my_book", chapter_id=1, section_id=1)
    result = freeze_section(tmp_path, request)

    assert result.action == "freeze_section_from_phase03_artifact"
    assert result.status == "success"
    assert result.request_id == request.request_id
    assert result.details["chapter_id"] == 1
    assert result.details["section_id"] == 1
    assert result.artifact_paths["boundary_artifact"].endswith("boundary.json")


def test_create_branch_action_returns_branch_scoped_emitted_result(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    init_request = build_initialize_workflow_request(tmp_path, "my_book")
    initialize_workflow(tmp_path, init_request)

    request = build_create_branch_request(tmp_path, "my_book", chapter=1, section=1, branch_id="rerun-sec1")
    result = create_branch_action(tmp_path, request)

    assert result.action == "create_branch"
    assert result.status == "success"
    assert result.request_id == request.request_id
    assert result.node.branch_id == "rerun-sec1"
    assert result.details["branch_role"] == "rerun"
    assert result.details["merge_operation"] == "promotion"


def test_create_assembly_branch_action_returns_branch_scoped_emitted_result(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    init_request = build_initialize_workflow_request(tmp_path, "my_book")
    initialize_workflow(tmp_path, init_request)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=build_create_branch_request(tmp_path, "my_book", chapter=1, section=1).selector,
        branch_id="fork-a",
        fork_group_id="fg-1",
    )
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=build_create_branch_request(tmp_path, "my_book", chapter=1, section=1).selector,
        branch_id="fork-b",
        fork_group_id="fg-1",
    )

    request = build_create_assembly_branch_request(
        "my_book",
        fork_group_id="fg-1",
        chapter_id=1,
        branch_id="assembly-ch1",
    )
    result = create_assembly_branch_action(tmp_path, request)

    assert result.action == "create_assembly_branch"
    assert result.status == "success"
    assert result.request_id == request.request_id
    assert result.node.branch_id == "assembly-ch1"
    assert result.details["fork_group_id"] == "fg-1"
    assert result.details["merge_operation"] == "assembly"
    assert result.details["branch_role"] == "assembly"


def test_discard_branch_action_returns_branch_scoped_emitted_result(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    init_request = build_initialize_workflow_request(tmp_path, "my_book")
    initialize_workflow(tmp_path, init_request)
    create_request = build_create_branch_request(tmp_path, "my_book", chapter=1, section=1, branch_id="rerun-sec1")
    create_branch_action(tmp_path, create_request)

    request = build_discard_branch_request("my_book", branch_id="rerun-sec1", reason="operator discard")
    result = discard_branch_action(tmp_path, request)

    assert result.action == "discard_branch"
    assert result.status == "hard_fail"
    assert result.request_id == request.request_id
    assert result.node.branch_id == "rerun-sec1"
    assert result.details["branch_id"] == "rerun-sec1"
    assert result.details["reason"] == "operator discard"


def test_promote_branch_action_returns_main_scoped_emitted_result(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    init_request = build_initialize_workflow_request(tmp_path, "my_book")
    initialize_workflow(tmp_path, init_request)
    create_request = build_create_branch_request(tmp_path, "my_book", chapter=1, section=1, branch_id="rerun-sec1")
    create_branch_action(tmp_path, create_request)
    rerun_freeze_section_on_branch(
        workspace=tmp_path,
        book_id="my_book",
        branch_id="rerun-sec1",
        chapter_id=1,
        section_id=1,
    )

    request = build_promote_branch_request("my_book", branch_id="rerun-sec1")
    result = promote_branch_action(tmp_path, request)

    assert result.action == "promote_branch_to_main"
    assert result.status == "success"
    assert result.request_id == request.request_id
    assert result.node.branch_id == "main"
    assert result.details["source_branch_id"] == "rerun-sec1"
    assert result.details["canonical_change_status"] == "canonical"


def test_record_assembly_validation_action_returns_branch_scoped_emitted_result(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    init_request = build_initialize_workflow_request(tmp_path, "my_book")
    initialize_workflow(tmp_path, init_request)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=build_create_branch_request(tmp_path, "my_book", chapter=1, section=1).selector,
        branch_id="fork-a",
        fork_group_id="fg-1",
    )
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=build_create_branch_request(tmp_path, "my_book", chapter=1, section=1).selector,
        branch_id="fork-b",
        fork_group_id="fg-1",
    )
    assembly = create_assembly_branch(tmp_path, "my_book", "fg-1", chapter_id=1)

    request = build_record_assembly_validation_request(
        "my_book",
        branch_id=assembly.branch_id,
        passed=False,
        message="Seam audit failed.",
    )
    result = record_assembly_validation_action(tmp_path, request)

    assert result.action == "record_assembly_validation"
    assert result.status == "integrity_degraded"
    assert result.request_id == request.request_id
    assert result.node.branch_id == assembly.branch_id
    assert result.details["validation_status"] == "failed"
    assert result.details["merge_operation"] == "assembly"


def test_finalize_chapter_action_returns_main_scoped_emitted_result(tmp_path: Path, monkeypatch) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)

    def _stub_finalize(book_root_arg: Path, outline_arg: dict, chapter_num: int) -> dict:
        assert chapter_num == 1
        return {
            "status": "finalized",
            "report_path": "draft/chapters/ch_001.seam_report.json",
            "original_path": "draft/chapters/ch_001.original.md",
            "fixed_path": "draft/chapters/ch_001.fixed.md",
            "provisional_path": None,
            "candidate_path": None,
            "final_path": "draft/chapters/ch_001.md",
            "repair_action_count": 0,
        }

    monkeypatch.setattr("bookforge.section_workflow.finalize_locked_chapter", _stub_finalize)

    init_request = build_initialize_workflow_request(tmp_path, "my_book")
    initialize_workflow(tmp_path, init_request)
    freeze_request = build_freeze_section_request(tmp_path, "my_book", chapter_id=1, section_id=1)
    freeze_section(tmp_path, freeze_request)
    _write_scene_artifacts(book_root, 1, 1, text="Rhea crossed the threshold.")
    lock_section_from_written_state(workspace=tmp_path, book_id="my_book", chapter_id=1, section_id=1)

    request = build_finalize_chapter_request(tmp_path, "my_book", chapter_id=1)
    result = finalize_chapter(tmp_path, request)

    assert result.action == "finalize_chapter_from_locked_sections"
    assert result.status == "no_op"
    assert result.request_id == request.request_id
    assert result.node.branch_id == "main"
    assert result.details["chapter_id"] == 1
    assert result.details["status"] == "finalized"
    assert result.artifact_paths["chapter_seam_report"].endswith("draft/chapters/ch_001.seam_report.json")
    assert result.artifact_paths["chapter_final_markdown"].endswith("draft/chapters/ch_001.md")


def test_lock_section_action_returns_main_scoped_emitted_result(tmp_path: Path, monkeypatch) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)

    def _stub_finalize(book_root_arg: Path, outline_arg: dict, chapter_num: int) -> dict:
        assert chapter_num == 1
        return {
            "status": "finalized",
            "report_path": "draft/chapters/ch_001.seam_report.json",
            "original_path": "draft/chapters/ch_001.original.md",
            "fixed_path": "draft/chapters/ch_001.fixed.md",
            "provisional_path": None,
            "candidate_path": None,
            "final_path": "draft/chapters/ch_001.md",
            "repair_action_count": 0,
        }

    monkeypatch.setattr("bookforge.section_workflow.finalize_locked_chapter", _stub_finalize)

    init_request = build_initialize_workflow_request(tmp_path, "my_book")
    initialize_workflow(tmp_path, init_request)
    freeze_request = build_freeze_section_request(tmp_path, "my_book", chapter_id=1, section_id=1)
    freeze_section(tmp_path, freeze_request)
    _write_scene_artifacts(book_root, 1, 1, text="Rhea crossed the threshold.")

    request = build_lock_section_request(tmp_path, "my_book", chapter_id=1, section_id=1)
    result = lock_section(tmp_path, request)

    assert result.action == "lock_section_from_written_state"
    assert result.status == "success"
    assert result.request_id == request.request_id
    assert result.node.branch_id == "main"
    assert result.details["chapter_id"] == 1
    assert result.details["section_id"] == 1
    assert result.details["status"] == "locked"
    assert result.artifact_paths["chapter_seam_report"].endswith("draft/chapters/ch_001.seam_report.json")


def test_lock_section_action_on_branch_writes_only_branch_snapshot(tmp_path: Path, monkeypatch) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)

    def _stub_finalize(book_root_arg: Path, outline_arg: dict, chapter_num: int) -> dict:
        assert book_root_arg.name == "snapshot"
        assert chapter_num == 1
        return {
            "status": "finalized",
            "report_path": "draft/chapters/ch_001.seam_report.json",
            "original_path": "draft/chapters/ch_001.original.md",
            "fixed_path": "draft/chapters/ch_001.fixed.md",
            "provisional_path": None,
            "candidate_path": None,
            "final_path": "draft/chapters/ch_001.md",
            "repair_action_count": 0,
        }

    monkeypatch.setattr("bookforge.execution.materialize.finalize_locked_chapter", _stub_finalize)

    init_request = build_initialize_workflow_request(tmp_path, "my_book")
    initialize_workflow(tmp_path, init_request)
    freeze_request = build_freeze_section_request(tmp_path, "my_book", chapter_id=1, section_id=1)
    freeze_section(tmp_path, freeze_request)
    create_request = build_create_branch_request(tmp_path, "my_book", chapter=1, section=1, branch_id="rewrite-sec1")
    create_branch_action(tmp_path, create_request)
    branch_root = supervision_paths.branch_snapshot_root(book_root, "rewrite-sec1")
    _write_scene_artifacts(branch_root, 1, 1, text="Branch-local section prose.")

    request = build_lock_section_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        section_id=1,
        branch_id="rewrite-sec1",
    )
    result = lock_section(tmp_path, request)
    main_registry = json.loads((book_root / "outline" / "snapshot_registry.json").read_text(encoding="utf-8"))
    branch_registry = json.loads((branch_root / "outline" / "snapshot_registry.json").read_text(encoding="utf-8"))
    branch_manifest = json.loads(supervision_paths.branch_manifest_path(book_root, "rewrite-sec1").read_text(encoding="utf-8"))

    assert result.action == "lock_section_from_written_state"
    assert result.status == "success"
    assert result.node.branch_id == "rewrite-sec1"
    assert result.details["branch_change_status"] == "changed"
    assert result.details["canonical_changed"] is False
    assert "canonical_change_status" not in result.details
    assert result.details["mutation_scope"] == "branch_authoritative"
    assert main_registry["chapters"][0]["sections"][0]["status"] == "frozen"
    assert branch_registry["chapters"][0]["sections"][0]["status"] == "locked"
    assert branch_manifest["lifecycle_state"] == "promote_ready"


def test_finalize_chapter_action_on_branch_writes_only_branch_snapshot(tmp_path: Path, monkeypatch) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)

    def _stub_finalize(book_root_arg: Path, outline_arg: dict, chapter_num: int) -> dict:
        assert book_root_arg.name == "snapshot"
        assert chapter_num == 1
        return {
            "status": "finalized",
            "report_path": "draft/chapters/ch_001.seam_report.json",
            "original_path": "draft/chapters/ch_001.original.md",
            "fixed_path": "draft/chapters/ch_001.fixed.md",
            "provisional_path": None,
            "candidate_path": None,
            "final_path": "draft/chapters/ch_001.md",
            "repair_action_count": 0,
        }

    monkeypatch.setattr("bookforge.execution.materialize.finalize_locked_chapter", _stub_finalize)

    init_request = build_initialize_workflow_request(tmp_path, "my_book")
    initialize_workflow(tmp_path, init_request)
    freeze_request = build_freeze_section_request(tmp_path, "my_book", chapter_id=1, section_id=1)
    freeze_section(tmp_path, freeze_request)
    create_request = build_create_branch_request(tmp_path, "my_book", chapter=1, section=1, branch_id="chapter-branch")
    create_branch_action(tmp_path, create_request)
    branch_root = supervision_paths.branch_snapshot_root(book_root, "chapter-branch")
    _write_scene_artifacts(branch_root, 1, 1, text="Branch-local chapter prose.")
    branch_outline_path = branch_root / "outline" / "outline.json"
    branch_registry_path = branch_root / "outline" / "snapshot_registry.json"
    branch_outline = json.loads(branch_outline_path.read_text(encoding="utf-8"))
    branch_registry = json.loads(branch_registry_path.read_text(encoding="utf-8"))
    branch_outline["chapters"][0]["sections"][0]["status"] = "locked"
    branch_registry["chapters"][0]["sections"][0]["status"] = "locked"
    branch_registry["chapters"][0]["chapter_status"] = "in_progress"
    branch_outline_path.write_text(json.dumps(branch_outline, ensure_ascii=True, indent=2), encoding="utf-8")
    branch_registry_path.write_text(json.dumps(branch_registry, ensure_ascii=True, indent=2), encoding="utf-8")

    request = build_finalize_chapter_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        branch_id="chapter-branch",
    )
    result = finalize_chapter(tmp_path, request)
    main_registry = json.loads((book_root / "outline" / "snapshot_registry.json").read_text(encoding="utf-8"))
    finalized_branch_registry = json.loads(branch_registry_path.read_text(encoding="utf-8"))

    assert result.action == "finalize_chapter_from_locked_sections"
    assert result.status == "success"
    assert result.node.branch_id == "chapter-branch"
    assert result.details["branch_change_status"] == "changed"
    assert result.details["canonical_changed"] is False
    assert "canonical_change_status" not in result.details
    assert result.details["mutation_scope"] == "branch_authoritative"
    assert main_registry["chapters"][0]["chapter_status"] != "finalized"
    assert finalized_branch_registry["chapters"][0]["chapter_status"] == "finalized"


def test_write_section_action_returns_main_scoped_emitted_result(tmp_path: Path, monkeypatch) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    init_request = build_initialize_workflow_request(tmp_path, "my_book")
    initialize_workflow(tmp_path, init_request)
    freeze_request = build_freeze_section_request(tmp_path, "my_book", chapter_id=1, section_id=1)
    freeze_section(tmp_path, freeze_request)

    def _stub_run_section_range(
        *,
        workspace,
        book_id,
        chapter_id,
        section_id,
        scene_start,
        scene_end,
        resume,
        ack_outline_attention_items,
        force_outline_gate_bypass,
    ):
        assert workspace == tmp_path
        assert book_id == "my_book"
        assert chapter_id == 1
        assert section_id == 1
        assert scene_start == 1
        assert scene_end == 1
        assert resume is False
        assert ack_outline_attention_items is True
        assert force_outline_gate_bypass is True
        _write_scene_artifacts(book_root, 1, 1, text="Rhea crossed the threshold.")

    monkeypatch.setattr("bookforge.execution.scoped.run_section_range", _stub_run_section_range)

    request = build_write_section_request(
        tmp_path,
        "my_book",
        chapter_id=1,
        section_id=1,
        ack_outline_attention_items=True,
        force_outline_gate_bypass=True,
    )
    result = write_frozen_section(tmp_path, request)

    assert result.action == "write_frozen_section"
    assert result.status == "no_op"
    assert result.request_id == request.request_id
    assert result.node.branch_id == "main"
    assert result.details["pre_reconciliation_status"] == "success"
    assert result.details["chapter_id"] == 1
    assert result.details["section_id"] == 1
    assert result.details["scene_ref_start"] == "1:1"
    assert result.details["scene_ref_end"] == "1:1"
