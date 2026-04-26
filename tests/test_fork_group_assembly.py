from __future__ import annotations

import json
from pathlib import Path

import pytest

from bookforge.branching import (
    branch_can_read_branch,
    create_assembly_branch,
    create_branch,
    load_branch_manifest,
    promote_branch_to_main,
    record_assembly_validation,
    validate_assembly_branch,
)
from bookforge.contracts import ScopeSelector
from bookforge.section_workflow import initialize_section_workflow
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
        json.dumps({"chapters": [{"chapter_id": 1, "title": "Opening", "goal": "Start the story.", "chapter_role": "hook", "stakes_shift": "Pressure escalates.", "bridge": {"from_prev": "", "to_next": "Move into danger."}, "pacing": {"intensity": 3, "tempo": "steady", "expected_scene_count": 2}}]}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    (run_dir / "outline_sections_v1.json").write_text(
        json.dumps({"chapters": [{"chapter_id": 1, "sections": [{"section_id": 1, "title": "Arrival", "intent": "Get inside.", "section_role": "setup", "target_scene_count": 1, "end_condition": "The door opens."}, {"section_id": 2, "title": "Breach", "intent": "Push deeper.", "section_role": "pressure", "target_scene_count": 1, "end_condition": "The threat appears."}]}]}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    (run_dir / "outline_final_v1_1.json").write_text(
        json.dumps({"schema_version": "1.1", "chapters": [{"chapter_id": 1, "title": "Opening", "sections": [{"section_id": 1, "title": "Arrival", "intent": "Get inside.", "end_condition": "The door opens.", "scenes": [{"scene_id": 1, "summary": "First scene.", "handoff_mode": "direct_continuation", "hands_off_to": "1:2", "transition_out_anchors": ["door"], "threads": []}]}, {"section_id": 2, "title": "Breach", "intent": "Push deeper.", "end_condition": "The threat appears.", "scenes": [{"scene_id": 2, "summary": "Second scene.", "handoff_mode": "terminal", "transition_out_anchors": ["shadow"], "threads": []}]}]}], "characters": [{"character_id": "rhea_mercer", "name": "Rhea Mercer", "role": "protagonist"}], "threads": []}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def _read_last_jsonl(path: Path) -> dict:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines
    return json.loads(lines[-1])


def _write_branch_scene(book_root: Path, branch_id: str, chapter: int, scene: int, text: str) -> None:
    branch_root = supervision_paths.branch_snapshot_root(book_root, branch_id)
    chapter_dir = branch_root / "draft" / "chapters" / f"ch_{int(chapter):03d}"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    (chapter_dir / f"scene_{int(scene):03d}.md").write_text(text, encoding="utf-8")
    (chapter_dir / f"scene_{int(scene):03d}.meta.json").write_text(
        json.dumps({"chapter": chapter, "scene": scene}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def test_fork_group_siblings_share_parent_and_cannot_cross_read(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)

    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=1),
        branch_id="fork-a",
        fork_group_id="fg-1",
    )
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=2),
        branch_id="fork-b",
        fork_group_id="fg-1",
    )

    left = load_branch_manifest(tmp_path, "my_book", "fork-a")
    right = load_branch_manifest(tmp_path, "my_book", "fork-b")

    assert left.fork_group_id == "fg-1"
    assert right.fork_group_id == "fg-1"
    assert left.parent_node.to_dict() == right.parent_node.to_dict()
    assert left.selector.section == 1
    assert right.selector.section == 2
    assert branch_can_read_branch(tmp_path, "my_book", "fork-a", "fork-b") is False


def test_create_assembly_branch_copies_scoped_writer_outputs_off_parent(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=1, scene=1),
        branch_id="fork-a",
        fork_group_id="fg-1",
        branch_role="writer",
    )
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=2, scene=2),
        branch_id="fork-b",
        fork_group_id="fg-1",
        branch_role="writer",
    )
    _write_branch_scene(book_root, "fork-a", 1, 1, "Fork A prose.")
    _write_branch_scene(book_root, "fork-b", 1, 2, "Fork B prose.")

    assembly = create_assembly_branch(tmp_path, "my_book", "fg-1", chapter_id=1, branch_id="assembly-ch1")
    assembly_root = supervision_paths.branch_snapshot_root(book_root, assembly.branch_id)

    assert (assembly_root / "draft" / "chapters" / "ch_001" / "scene_001.md").read_text(encoding="utf-8") == "Fork A prose."
    assert (assembly_root / "draft" / "chapters" / "ch_001" / "scene_002.md").read_text(encoding="utf-8") == "Fork B prose."
    assert not (book_root / "draft" / "chapters" / "ch_001" / "scene_001.md").exists()
    branch_execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root, assembly.branch_id))
    assert branch_execution_result["action"] == "assemble_fork_group_writer_outputs"
    assert branch_execution_result["details"]["copied_file_count"] == 4


def test_validate_assembly_branch_passes_when_sibling_outputs_are_staged(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=1, scene=1),
        branch_id="fork-a",
        fork_group_id="fg-1",
        branch_role="writer",
    )
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=2, scene=2),
        branch_id="fork-b",
        fork_group_id="fg-1",
        branch_role="writer",
    )
    _write_branch_scene(book_root, "fork-a", 1, 1, "Fork A prose.")
    _write_branch_scene(book_root, "fork-b", 1, 2, "Fork B prose.")
    assembly = create_assembly_branch(tmp_path, "my_book", "fg-1", chapter_id=1, branch_id="assembly-ch1")

    validated = validate_assembly_branch(tmp_path, "my_book", assembly.branch_id)

    assert validated.lifecycle_state == "assembled_pending_promotion"
    assert validated.validation_status == "passed"
    branch_execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root, assembly.branch_id))
    assert branch_execution_result["action"] == "validate_assembly_branch"
    assert branch_execution_result["status"] == "promotion_required"


def test_validated_writer_assembly_promotes_staged_outputs_to_main(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=1, scene=1),
        branch_id="fork-a",
        fork_group_id="fg-1",
        branch_role="writer",
    )
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_write", chapter=1, section=2, scene=2),
        branch_id="fork-b",
        fork_group_id="fg-1",
        branch_role="writer",
    )
    _write_branch_scene(book_root, "fork-a", 1, 1, "Fork A prose.")
    _write_branch_scene(book_root, "fork-b", 1, 2, "Fork B prose.")
    assembly = create_assembly_branch(tmp_path, "my_book", "fg-1", chapter_id=1, branch_id="assembly-ch1")
    validate_assembly_branch(tmp_path, "my_book", assembly.branch_id)

    promoted = promote_branch_to_main(tmp_path, "my_book", assembly.branch_id)

    assert promoted.lifecycle_state == "promoted"
    assert (book_root / "draft" / "chapters" / "ch_001" / "scene_001.md").read_text(encoding="utf-8") == "Fork A prose."
    assert (book_root / "draft" / "chapters" / "ch_001" / "scene_002.md").read_text(encoding="utf-8") == "Fork B prose."
    main_execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root, "main"))
    assert main_execution_result["action"] == "promote_branch_to_main"
    assert main_execution_result["details"]["source_branch_id"] == "assembly-ch1"


def test_create_assembly_branch_refuses_stale_parent_snapshot(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=1),
        branch_id="fork-a",
        fork_group_id="fg-1",
    )
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=2),
        branch_id="fork-b",
        fork_group_id="fg-1",
    )

    registry_path = book_root / "outline" / "snapshot_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["updated_at"] = "2030-01-01T00:00:00Z"
    registry_path.write_text(json.dumps(registry, ensure_ascii=True, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="stale against current main revision"):
        create_assembly_branch(tmp_path, "my_book", "fg-1", chapter_id=1)


def test_failed_assembly_validation_blocks_promotion(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=1),
        branch_id="fork-a",
        fork_group_id="fg-1",
    )
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=2),
        branch_id="fork-b",
        fork_group_id="fg-1",
    )

    assembly = create_assembly_branch(tmp_path, "my_book", "fg-1", chapter_id=1)
    record_assembly_validation(tmp_path, "my_book", assembly.branch_id, passed=False, message="Seam audit failed.")

    with pytest.raises(ValueError, match="cannot promote without passed validation"):
        promote_branch_to_main(tmp_path, "my_book", assembly.branch_id)


def test_assembly_validation_emits_branch_local_reconciliation(tmp_path: Path) -> None:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=1),
        branch_id="fork-a",
        fork_group_id="fg-1",
    )
    create_branch(
        workspace=tmp_path,
        book_id="my_book",
        selector=ScopeSelector(book_id="my_book", branch_id="main", workflow_family="section_local_outline", chapter=1, section=2),
        branch_id="fork-b",
        fork_group_id="fg-1",
    )

    assembly = create_assembly_branch(tmp_path, "my_book", "fg-1", chapter_id=1)
    record_assembly_validation(tmp_path, "my_book", assembly.branch_id, passed=False, message="Seam audit failed.")

    branch_execution_result = _read_last_jsonl(supervision_paths.execution_results_path(book_root, assembly.branch_id))

    assert branch_execution_result["action"] == "record_assembly_validation"
    assert branch_execution_result["status"] == "integrity_degraded"
    assert branch_execution_result["details"]["pre_reconciliation_status"] == "integrity_degraded"
    assert branch_execution_result["details"]["branch_change_status"] == "changed"
    assert branch_execution_result["details"]["integrity_change"] == "worsened"
    assert branch_execution_result["details"]["validation_status"] == "failed"
    assert "canonical_change_status" not in branch_execution_result["details"]
