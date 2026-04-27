from __future__ import annotations

import json
from pathlib import Path

from bookforge.contracts import ScopeSelector
from bookforge.cli import build_parser
from bookforge.execution import (
    build_create_recovery_branch_request,
    build_recovery_branch_request,
    create_recovery_branch,
    invalidate_scope_outputs,
    normalize_outline_scope,
    promote_recovery_branch,
    quarantine_artifacts,
    rebuild_state_scope,
    redraft_scope,
    validate_recovery_branch,
)
from bookforge.query import get_outline_lineage_audit, legal_next_actions, list_execution_options
from bookforge.query.recovery import (
    get_recovery_branch_health,
    get_recovery_manifest,
    get_recovery_plan_readiness,
    get_scope_invalidation_preview,
    get_state_rebuild_preview,
)
from bookforge.section_workflow import initialize_section_workflow
from bookforge.supervision import paths as supervision_paths
from bookforge.workspace import init_book_workspace


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
    registry = _read_json(registry_path)
    registry["chapters"][0]["sections"][0]["status"] = "frozen"
    registry["chapters"][0]["sections"][0]["scene_ref_start"] = "1:1"
    registry["chapters"][0]["sections"][0]["scene_ref_end"] = "1:2"
    _write_json(registry_path, registry)


def _write_polluted_draft_outputs(book_root: Path) -> None:
    chapter_dir = book_root / "draft" / "chapters" / "ch_001"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    for scene_id in (1, 2):
        (chapter_dir / f"scene_{scene_id:03d}.md").write_text(f"Polluted scene {scene_id}.", encoding="utf-8")
        _write_json(chapter_dir / f"scene_{scene_id:03d}.meta.json", {"scene_id": scene_id})
    (book_root / "draft" / "chapters" / "ch_001.md").write_text("Polluted chapter.", encoding="utf-8")
    _write_json(
        book_root / "state.json",
        {
            "schema_version": "1.0",
            "status": "WRITING",
            "cursor": {"chapter": 1, "scene": 2},
            "world": {"recent_facts": ["Artie and Vex are here."], "open_threads": ["thread_wrong"]},
            "summary": {"story_so_far": ["Ghost outline happened."], "must_stay_true": ["Vex exists."]},
            "budgets": {"tokens": 123},
        },
    )
    _write_json(
        book_root / "draft" / "context" / "characters" / "index.json",
        {
            "characters": [
                {"character_id": "char_artie", "state_path": "draft/context/characters/artie.state.json"},
                {"character_id": "rhea_mercer", "state_path": "draft/context/characters/rhea.state.json"},
            ]
        },
    )
    _write_json(
        book_root / "draft" / "context" / "characters" / "artie.state.json",
        {"character_id": "char_artie", "name": "Artie", "last_touched": {"chapter": 1, "scene": 2}},
    )
    _write_json(
        book_root / "draft" / "context" / "characters" / "rhea.state.json",
        {"character_id": "rhea_mercer", "name": "Rhea", "inventory": [{"item": "polluted"}], "last_touched": {"chapter": 1, "scene": 2}},
    )
    _write_json(book_root / "draft" / "context" / "chapter_summaries" / "ch_001.json", {"key_events": ["polluted"]})
    _write_json(book_root / "draft" / "context" / "settings" / "ch_001" / "scene_001" / "prose_extracted.setting.json", {"location": "polluted"})
    _write_json(book_root / "draft" / "context" / "phase_history" / "ch001_sc001.json", {"phases": {"write": {"status": "success"}}})
    _write_json(book_root / "draft" / "context" / "item_registry.json", {"items": [{"item_id": "ITEM_WRONG"}]})


def _create_recovery_branch(tmp_path: Path, branch_id: str = "recover-sec1") -> None:
    request = build_create_recovery_branch_request(
        tmp_path,
        "my_book",
        anchor_type="declared_source_run",
        source_run_id="run_001",
        branch_id=branch_id,
    )
    result = create_recovery_branch(tmp_path, request)
    assert result.status == "success"
    assert result.details["branch_id"] == branch_id


def test_recovery_branch_snapshots_evidence_and_exposes_legal_actions(tmp_path: Path) -> None:
    book_root = _setup_initialized_book(tmp_path)
    _introduce_lineage_drift(book_root)
    _write_polluted_draft_outputs(book_root)

    main_selector = ScopeSelector(book_id="my_book", branch_id="main", chapter=1, section=1)
    main_actions = {option.action: option for option in list_execution_options(tmp_path, main_selector, prefer_emitted=False)}
    assert main_actions["create_recovery_branch"].allowed is True
    assert main_actions["create_recovery_branch"].details["approval_required"] is True
    assert "recovery anchor selection" in main_actions["create_recovery_branch"].details["approval_reasons"]

    _create_recovery_branch(tmp_path)

    branch_root = supervision_paths.branch_snapshot_root(book_root, "recover-sec1")
    assert (branch_root / "outline" / "pipeline_runs" / "run_001" / "outline_final_v1_1.json").exists()
    assert (branch_root / "outline" / "section_drafts" / "ch_001_sec_001_phase03.json").exists()
    manifest = get_recovery_manifest(tmp_path, "my_book", branch_id="recover-sec1")
    assert manifest["scope"]["affected_scopes"] == [{"chapter_id": 1, "section_id": 1}]
    assert manifest["scope_output_ranges"]["ch_001_sec_001"]["scene_ids"] == [1, 2]

    branch_selector = ScopeSelector(book_id="my_book", branch_id="recover-sec1", chapter=1, section=1)
    branch_actions = {option.action: option for option in list_execution_options(tmp_path, branch_selector, prefer_emitted=False)}
    legal = [option.action for option in legal_next_actions(tmp_path, branch_selector, prefer_emitted=False)]
    assert "quarantine_artifacts" in legal
    assert "normalize_outline_scope" in legal
    assert "validate_recovery_branch" not in legal
    assert branch_actions["quarantine_artifacts"].details["approval_required"] is True
    assert "destructive cleanup/quarantine" in branch_actions["quarantine_artifacts"].details["approval_reasons"]

    readiness = get_recovery_plan_readiness(tmp_path, "my_book", branch_id="recover-sec1")
    assert readiness["recommended_next_action"] == "normalize_outline_scope"
    assert readiness["approval_required"] is True


def test_recovery_branch_quarantines_normalizes_invalidates_redrafts_validates_and_promotes(tmp_path: Path, monkeypatch) -> None:
    book_root = _setup_initialized_book(tmp_path)
    _introduce_lineage_drift(book_root)
    _write_polluted_draft_outputs(book_root)
    _create_recovery_branch(tmp_path)

    branch_root = supervision_paths.branch_snapshot_root(book_root, "recover-sec1")
    quarantine_result = quarantine_artifacts(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="quarantine_artifacts", branch_id="recover-sec1"),
    )
    assert quarantine_result.status == "success"
    assert not (branch_root / "outline" / "section_drafts" / "ch_001_sec_001_phase03.json").exists()
    assert (book_root / "outline" / "section_drafts" / "ch_001_sec_001_phase03.json").exists()

    normalize_result = normalize_outline_scope(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="normalize_outline_scope", branch_id="recover-sec1"),
    )
    assert normalize_result.status == "success"
    branch_outline = _read_json(branch_root / "outline" / "outline.json")
    assert branch_outline["characters"] == [{"character_id": "rhea_mercer", "name": "Rhea Mercer"}]
    assert len(branch_outline["chapters"][0]["sections"][0]["scenes"]) == 1

    preview = get_scope_invalidation_preview(tmp_path, "my_book", branch_id="recover-sec1")
    assert "draft/chapters/ch_001/scene_001.md" in preview["candidate_paths"]
    assert "draft/chapters/ch_001/scene_002.md" in preview["candidate_paths"]

    invalidate_result = invalidate_scope_outputs(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="invalidate_scope_outputs", branch_id="recover-sec1"),
    )
    assert invalidate_result.status == "success"
    assert not (branch_root / "draft" / "chapters" / "ch_001" / "scene_002.md").exists()
    assert (book_root / "draft" / "chapters" / "ch_001" / "scene_002.md").exists()

    blocked_validate = validate_recovery_branch(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="validate_recovery_branch", branch_id="recover-sec1"),
    )
    assert blocked_validate.status == "integrity_degraded"
    assert "rebuild_state_scope has not completed" in blocked_validate.details["recovery_receipt"]["details"]["blockers"]

    state_preview = get_state_rebuild_preview(tmp_path, "my_book", branch_id="recover-sec1")
    assert "state.json" in state_preview["candidate_paths"]
    assert "draft/context/characters/artie.state.json" in state_preview["candidate_paths"]
    assert "draft/context/settings/ch_001/scene_001/prose_extracted.setting.json" in state_preview["candidate_paths"]

    rebuild_result = rebuild_state_scope(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="rebuild_state_scope", branch_id="recover-sec1"),
    )
    assert rebuild_result.status == "success"
    branch_state = _read_json(branch_root / "state.json")
    assert branch_state["summary"]["story_so_far"] == []
    assert branch_state["world"]["recent_facts"] == []
    assert not (branch_root / "draft" / "context" / "characters" / "artie.state.json").exists()
    rebuilt_index = _read_json(branch_root / "draft" / "context" / "characters" / "index.json")
    assert [entry["character_id"] for entry in rebuilt_index["characters"]] == ["rhea_mercer"]

    blocked_after_rebuild = validate_recovery_branch(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="validate_recovery_branch", branch_id="recover-sec1"),
    )
    assert blocked_after_rebuild.status == "integrity_degraded"
    assert "redraft_scope has not completed" in blocked_after_rebuild.details["recovery_receipt"]["details"]["blockers"]

    def _fake_run_section_range(*args, **kwargs):
        root = supervision_paths.branch_snapshot_root(book_root, kwargs["branch_id"])
        chapter_dir = root / "draft" / "chapters" / f"ch_{int(kwargs['chapter_id']):03d}"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        for scene_id in range(int(kwargs["scene_start"]), int(kwargs["scene_end"]) + 1):
            (chapter_dir / f"scene_{scene_id:03d}.md").write_text(f"Recovered scene {scene_id}.", encoding="utf-8")
            _write_json(chapter_dir / f"scene_{scene_id:03d}.meta.json", {"scene_id": scene_id, "recovered": True})

    monkeypatch.setattr("bookforge.execution.scoped.run_section_range", _fake_run_section_range)
    redraft_result = redraft_scope(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="redraft_scope", branch_id="recover-sec1"),
    )
    assert redraft_result.status == "success"
    assert (branch_root / "draft" / "chapters" / "ch_001" / "scene_001.md").read_text(encoding="utf-8") == "Recovered scene 1."
    assert not (branch_root / "draft" / "chapters" / "ch_001" / "scene_002.md").exists()

    validate_result = validate_recovery_branch(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="validate_recovery_branch", branch_id="recover-sec1"),
    )
    assert validate_result.status == "success"
    health = get_recovery_branch_health(tmp_path, "my_book", branch_id="recover-sec1")
    assert health.status == "healthy"
    assert health.details["recommended_next_action"] == "promote_recovery_branch"
    assert "promotion to main" in health.details["approval_reasons"]

    promote_result = promote_recovery_branch(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="promote_recovery_branch", branch_id="recover-sec1"),
    )
    assert promote_result.status == "success"
    assert not (book_root / "outline" / "section_drafts" / "ch_001_sec_001_phase03.json").exists()
    assert not (book_root / "draft" / "chapters" / "ch_001" / "scene_002.md").exists()
    assert (book_root / "draft" / "chapters" / "ch_001" / "scene_001.md").read_text(encoding="utf-8") == "Recovered scene 1."
    assert not (book_root / "draft" / "context" / "characters" / "artie.state.json").exists()
    main_index = _read_json(book_root / "draft" / "context" / "characters" / "index.json")
    assert [entry["character_id"] for entry in main_index["characters"]] == ["rhea_mercer"]
    assert get_outline_lineage_audit(tmp_path, "my_book").status == "healthy"


def test_latest_outline_run_anchor_uses_latest_pointer(tmp_path: Path) -> None:
    book_root = _setup_initialized_book(tmp_path)
    _introduce_lineage_drift(book_root)
    latest_payload = _outline_payload(characters=["vance_harrow"], scene_count=1)
    _write_json(book_root / "outline" / "pipeline_latest.json", {"run_id": "run_002"})
    _write_json(book_root / "outline" / "pipeline_runs" / "run_002" / "outline_final_v1_1.json", latest_payload)

    request = build_create_recovery_branch_request(
        tmp_path,
        "my_book",
        anchor_type="latest_outline_run",
        branch_id="recover-latest",
    )
    create_recovery_branch(tmp_path, request)
    quarantine_artifacts(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="quarantine_artifacts", branch_id="recover-latest"),
    )
    normalize_outline_scope(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="normalize_outline_scope", branch_id="recover-latest"),
    )

    branch_root = supervision_paths.branch_snapshot_root(book_root, "recover-latest")
    branch_outline = _read_json(branch_root / "outline" / "outline.json")
    assert branch_outline["characters"] == [{"character_id": "vance_harrow", "name": "Vance Harrow"}]


def test_cli_parser_accepts_recovery_workflow_commands() -> None:
    parser = build_parser()

    create_args = parser.parse_args(
        [
            "--workspace",
            "workspace",
            "workflow",
            "create-recovery-branch",
            "--book",
            "my_book",
            "--branch-id",
            "recover-sec1",
            "--anchor-type",
            "declared_source_run",
            "--source-run-id",
            "run_001",
            "--affected-scope",
            "1:1",
            "--salvage-policy",
            "reference_only",
        ]
    )
    assert create_args.workflow_command == "create-recovery-branch"
    assert create_args.anchor_type == "declared_source_run"
    assert create_args.affected_scope == ["1:1"]

    for command in (
        "quarantine-artifacts",
        "normalize-outline-scope",
        "invalidate-scope-outputs",
        "state-rebuild-preview",
        "rebuild-state-scope",
        "redraft-scope",
        "validate-recovery-branch",
        "promote-recovery-branch",
        "recovery-health",
        "recovery-readiness",
        "scope-invalidation-preview",
    ):
        args = parser.parse_args(
            [
                "--workspace",
                "workspace",
                "workflow",
                command,
                "--book",
                "my_book",
                "--branch-id",
                "recover-sec1",
            ]
        )
        assert args.workflow_command == command
        assert args.branch_id == "recover-sec1"
