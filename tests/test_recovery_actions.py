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
    review_downstream_dependencies,
    review_recovery_semantics,
    validate_recovery_branch,
)
from bookforge.query import get_outline_lineage_audit, legal_next_actions, list_execution_options
from bookforge.query.recovery import (
    get_downstream_dependency_review,
    get_recovery_branch_health,
    get_recovery_blast_radius,
    get_recovery_manifest,
    get_recovery_plan_readiness,
    get_recovery_semantic_review,
    get_recovery_semantic_review_readiness,
    get_scope_invalidation_preview,
    get_state_rebuild_preview,
    recovery_manifest_path,
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


def _multi_chapter_outline_payload() -> dict:
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
                        "intent": "Rhea enters the ledger vault.",
                        "end_condition": "The vault door opens.",
                        "scenes": [_scene(1, "Rhea opens the vault.", ["rhea_mercer"])],
                    }
                ],
            },
            {
                "chapter_id": 2,
                "title": "Accounting",
                "sections": [
                    {
                        "section_id": 1,
                        "title": "Audit",
                        "intent": "Vance audits the debt engine.",
                        "end_condition": "The account mismatch is exposed.",
                        "scenes": [_scene(1, "Vance finds the mismatch.", ["rhea_mercer", "vance_harrow"])],
                    }
                ],
            },
        ],
        "characters": [
            {"character_id": "rhea_mercer", "name": "Rhea Mercer"},
            {"character_id": "vance_harrow", "name": "Vance Harrow"},
        ],
        "threads": [],
    }


def _write_run_artifacts(book_root: Path, run_id: str = "run_001", payload: dict | None = None) -> None:
    outline_payload = payload or _outline_payload()
    outline_root = book_root / "outline"
    run_dir = outline_root / "pipeline_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(outline_root / "pipeline_latest.json", {"run_id": run_id})
    _write_json(
        run_dir / "outline_spine_v1.json",
        {"chapters": [{"chapter_id": chapter.get("chapter_id"), "title": chapter.get("title")} for chapter in outline_payload.get("chapters", [])]},
    )
    _write_json(
        run_dir / "outline_sections_v1.json",
        {
            "chapters": [
                {
                    "chapter_id": chapter.get("chapter_id"),
                    "sections": [
                        {
                            "section_id": section.get("section_id"),
                            "title": section.get("title"),
                            "intent": section.get("intent"),
                            "end_condition": section.get("end_condition"),
                        }
                        for section in chapter.get("sections", [])
                    ],
                }
                for chapter in outline_payload.get("chapters", [])
            ]
        },
    )
    _write_json(run_dir / "outline_final_v1_1.json", outline_payload)


def _setup_initialized_book(tmp_path: Path) -> Path:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root)
    initialize_section_workflow(workspace=tmp_path, book_id="my_book", overwrite=True)
    return book_root


def _setup_initialized_multi_chapter_book(tmp_path: Path) -> Path:
    book_root = _init_book(tmp_path)
    _write_run_artifacts(book_root, payload=_multi_chapter_outline_payload())
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


def _introduce_multi_chapter_lineage_drift(book_root: Path) -> None:
    outline_root = book_root / "outline"
    polluted = _multi_chapter_outline_payload()
    polluted["characters"] = [
        {"character_id": "rhea_mercer", "name": "Rhea Mercer"},
        {"character_id": "vance_harrow", "name": "Vance Harrow"},
        {"character_id": "char_artie", "name": "Artie"},
    ]
    for chapter in polluted["chapters"]:
        section = chapter["sections"][0]
        section["scenes"].append(_scene(2, f"Artie contaminates chapter {chapter['chapter_id']}.", ["char_artie"]))
    _write_json(outline_root / "outline.json", polluted)
    for chapter_id in (1, 2):
        _write_json(outline_root / "section_drafts" / f"ch_{chapter_id:03d}_sec_001_phase03.json", polluted)
    registry_path = outline_root / "snapshot_registry.json"
    registry = _read_json(registry_path)
    for chapter in registry["chapters"]:
        chapter["chapter_status"] = "in_progress"
        for section in chapter["sections"]:
            section["status"] = "frozen"
            section["scene_ref_start"] = f"{chapter['chapter_id']}:1"
            section["scene_ref_end"] = f"{chapter['chapter_id']}:2"
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


def _write_multi_chapter_polluted_outputs(book_root: Path) -> None:
    for chapter_id in (1, 2):
        chapter_dir = book_root / "draft" / "chapters" / f"ch_{chapter_id:03d}"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        for scene_id in (1, 2):
            (chapter_dir / f"scene_{scene_id:03d}.md").write_text(f"Polluted chapter {chapter_id} scene {scene_id}.", encoding="utf-8")
            _write_json(chapter_dir / f"scene_{scene_id:03d}.meta.json", {"chapter_id": chapter_id, "scene_id": scene_id})
        (book_root / "draft" / "chapters" / f"ch_{chapter_id:03d}.md").write_text(f"Polluted chapter {chapter_id}.", encoding="utf-8")
        _write_json(book_root / "draft" / "context" / "chapter_summaries" / f"ch_{chapter_id:03d}.json", {"key_events": ["char_artie polluted this chapter"]})
        _write_json(
            book_root / "draft" / "context" / "settings" / f"ch_{chapter_id:03d}" / "scene_001" / "prose_extracted.setting.json",
            {"node": {"branch_id": "main"}, "setting": {"characters": ["char_artie"]}},
        )
    _write_json(
        book_root / "state.json",
        {
            "schema_version": "1.0",
            "status": "WRITING",
            "cursor": {"chapter": 2, "scene": 2},
            "world": {"recent_facts": ["Artie contaminated both chapters."], "open_threads": ["thread_wrong"]},
            "summary": {"story_so_far": ["Two chapters bled together."], "must_stay_true": ["Artie exists."]},
            "budgets": {"tokens": 123},
        },
    )
    _write_json(
        book_root / "draft" / "context" / "characters" / "index.json",
        {
            "characters": [
                {"character_id": "rhea_mercer", "state_path": "draft/context/characters/rhea_mercer.state.json"},
                {"character_id": "vance_harrow", "state_path": "draft/context/characters/vance_harrow.state.json"},
                {"character_id": "char_artie", "state_path": "draft/context/characters/artie.state.json"},
            ]
        },
    )
    _write_json(book_root / "draft" / "context" / "characters" / "artie.state.json", {"character_id": "char_artie", "name": "Artie"})
    _write_json(book_root / "draft" / "context" / "characters" / "rhea_mercer.state.json", {"character_id": "rhea_mercer", "name": "Rhea"})
    _write_json(book_root / "draft" / "context" / "characters" / "vance_harrow.state.json", {"character_id": "vance_harrow", "name": "Vance"})


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


def _postcondition(result) -> dict:
    return result.details["recovery_receipt"]["details"]["postcondition"]


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
    manifest["scope"]["downstream_scopes"] = [{"chapter_id": 2, "section_id": 1}]
    manifest["scope_output_ranges"]["ch_002_sec_001"] = {"chapter_id": 2, "section_id": 1, "scene_ids": [1]}
    _write_json(recovery_manifest_path(book_root, "recover-sec1"), manifest)
    downstream_chapter_dir = branch_root / "draft" / "chapters" / "ch_002"
    downstream_chapter_dir.mkdir(parents=True, exist_ok=True)
    (downstream_chapter_dir / "scene_001.md").write_text("Downstream scene needs review.", encoding="utf-8")
    _write_json(downstream_chapter_dir / "scene_001.meta.json", {"chapter_id": 2, "scene_id": 1})

    branch_selector = ScopeSelector(book_id="my_book", branch_id="recover-sec1", chapter=1, section=1)
    branch_actions = {option.action: option for option in list_execution_options(tmp_path, branch_selector, prefer_emitted=False)}
    legal = [option.action for option in legal_next_actions(tmp_path, branch_selector, prefer_emitted=False)]
    assert "quarantine_artifacts" in legal
    assert "normalize_outline_scope" in legal
    assert "validate_recovery_branch" not in legal
    assert branch_actions["quarantine_artifacts"].details["approval_required"] is True
    assert "destructive cleanup/quarantine" in branch_actions["quarantine_artifacts"].details["approval_reasons"]
    assert "scope output invalidation" in branch_actions["invalidate_scope_outputs"].details["approval_reasons"]
    assert "state/projection rebuild" in branch_actions["rebuild_state_scope"].details["approval_reasons"]
    assert "scope redraft" in branch_actions["redraft_scope"].details["approval_reasons"]
    assert "promotion to main" in branch_actions["promote_recovery_branch"].details["approval_reasons"]
    assert branch_actions["review_recovery_semantics"].allowed is False
    assert "missing successful receipt: redraft_scope" in branch_actions["review_recovery_semantics"].refusal_reason
    assert branch_actions["review_downstream_dependencies"].allowed is False
    assert "missing successful receipt: redraft_scope" in branch_actions["review_downstream_dependencies"].refusal_reason

    readiness = get_recovery_plan_readiness(tmp_path, "my_book", branch_id="recover-sec1")
    assert readiness["recommended_next_action"] == "normalize_outline_scope"
    assert readiness["approval_required"] is True
    semantic_readiness = get_recovery_semantic_review_readiness(tmp_path, "my_book", branch_id="recover-sec1")
    assert semantic_readiness["ready"] is False
    assert semantic_readiness["artifact_status"] == "diagnostic"
    assert semantic_readiness["mutation_scope"] == "diagnostic_only"
    assert "missing successful receipt: redraft_scope" in semantic_readiness["blockers"]
    assert "missing successful receipt: validate_recovery_branch" in semantic_readiness["blockers"]

    blast_radius = get_recovery_blast_radius(tmp_path, "my_book", branch_id="recover-sec1")
    assert blast_radius["scope_groups"]["affected"] == [{"chapter_id": 1, "section_id": 1}]
    assert blast_radius["scope_groups"]["downstream"] == [{"chapter_id": 2, "section_id": 1}]
    assert blast_radius["scope_groups"]["prose_invalidation_scope"] == [{"chapter_id": 1, "section_id": 1}]
    assert blast_radius["scope_groups"]["state_rebuild_scope"] == [
        {"chapter_id": 1, "section_id": 1},
        {"chapter_id": 2, "section_id": 1},
    ]
    assert blast_radius["scope_groups"]["downstream_trace_status"] == "manifest_declared_only"
    assert blast_radius["families"]["downstream_review"]["candidate_count"] == 2
    assert blast_radius["families"]["downstream_review"]["mutation_supported"] is False
    assert "author_review_downstream_scope" in blast_radius["families"]["downstream_review"]["recommended_actions"]
    downstream_review = get_downstream_dependency_review(tmp_path, "my_book", branch_id="recover-sec1")
    assert downstream_review["status"] == "manifest_declared_only"
    assert downstream_review["downstream_scopes"] == [{"chapter_id": 2, "section_id": 1}]
    assert len(downstream_review["candidate_artifacts"]) == 2
    assert downstream_review["recommended_next_action"] == "review_downstream_dependencies"


def test_recovery_branch_supports_explicit_multi_scope_radius(tmp_path: Path) -> None:
    book_root = _setup_initialized_book(tmp_path)
    _introduce_lineage_drift(book_root)
    _write_polluted_draft_outputs(book_root)

    request = build_create_recovery_branch_request(
        tmp_path,
        "my_book",
        anchor_type="declared_source_run",
        source_run_id="run_001",
        affected_scopes=[{"chapter_id": 1, "section_id": 1}, {"chapter_id": 2, "section_id": 1}],
        branch_id="recover-wide",
    )
    result = create_recovery_branch(tmp_path, request)
    assert result.status == "success"

    manifest = get_recovery_manifest(tmp_path, "my_book", branch_id="recover-wide")
    assert manifest["scope"]["affected_scopes"] == [{"chapter_id": 1, "section_id": 1}, {"chapter_id": 2, "section_id": 1}]
    assert manifest["scope_output_ranges"]["ch_001_sec_001"]["scene_ids"] == [1, 2]
    assert manifest["scope_output_ranges"]["ch_002_sec_001"]["scene_ids"] == []

    branch_selector = ScopeSelector(book_id="my_book", branch_id="recover-wide", chapter=1, section=1)
    branch_actions = {option.action: option for option in list_execution_options(tmp_path, branch_selector, prefer_emitted=False)}
    assert "broad recovery radius" in branch_actions["quarantine_artifacts"].details["approval_reasons"]
    assert "broad recovery radius" in branch_actions["redraft_scope"].details["approval_reasons"]

    blast_radius = get_recovery_blast_radius(tmp_path, "my_book", branch_id="recover-wide")
    assert blast_radius["scope_groups"]["affected"] == [
        {"chapter_id": 1, "section_id": 1},
        {"chapter_id": 2, "section_id": 1},
    ]
    assert blast_radius["scope_groups"]["state_rebuild_scope"] == blast_radius["scope_groups"]["affected"]
    assert blast_radius["scope_groups"]["downstream_trace_status"] == "none_declared"


def test_recovery_branch_repairs_multi_chapter_pollution_end_to_end(tmp_path: Path, monkeypatch) -> None:
    book_root = _setup_initialized_multi_chapter_book(tmp_path)
    _introduce_multi_chapter_lineage_drift(book_root)
    _write_multi_chapter_polluted_outputs(book_root)

    request = build_create_recovery_branch_request(
        tmp_path,
        "my_book",
        anchor_type="declared_source_run",
        source_run_id="run_001",
        affected_scopes=[{"chapter_id": 1, "section_id": 1}, {"chapter_id": 2, "section_id": 1}],
        branch_id="recover-two-chapters",
    )
    create_recovery_branch(tmp_path, request)
    branch_root = supervision_paths.branch_snapshot_root(book_root, "recover-two-chapters")

    quarantine_artifacts(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="quarantine_artifacts", branch_id="recover-two-chapters"),
    )
    normalize_outline_scope(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="normalize_outline_scope", branch_id="recover-two-chapters"),
    )
    branch_outline = _read_json(branch_root / "outline" / "outline.json")
    assert [item["character_id"] for item in branch_outline["characters"]] == ["rhea_mercer", "vance_harrow"]
    assert len(branch_outline["chapters"][0]["sections"][0]["scenes"]) == 1
    assert len(branch_outline["chapters"][1]["sections"][0]["scenes"]) == 1

    preview = get_scope_invalidation_preview(tmp_path, "my_book", branch_id="recover-two-chapters")
    assert "draft/chapters/ch_001/scene_002.md" in preview["candidate_paths"]
    assert "draft/chapters/ch_002/scene_002.md" in preview["candidate_paths"]

    invalidate_scope_outputs(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="invalidate_scope_outputs", branch_id="recover-two-chapters"),
    )
    assert not (branch_root / "draft" / "chapters" / "ch_001" / "scene_002.md").exists()
    assert not (branch_root / "draft" / "chapters" / "ch_002" / "scene_002.md").exists()

    rebuild_state_scope(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="rebuild_state_scope", branch_id="recover-two-chapters"),
    )
    rebuilt_index = _read_json(branch_root / "draft" / "context" / "characters" / "index.json")
    assert [entry["character_id"] for entry in rebuilt_index["characters"]] == ["rhea_mercer", "vance_harrow"]
    assert not (branch_root / "draft" / "context" / "characters" / "artie.state.json").exists()

    def _fake_run_section_range(*args, **kwargs):
        root = supervision_paths.branch_snapshot_root(book_root, kwargs["branch_id"])
        chapter_id = int(kwargs["chapter_id"])
        chapter_dir = root / "draft" / "chapters" / f"ch_{chapter_id:03d}"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        for scene_id in range(int(kwargs["scene_start"]), int(kwargs["scene_end"]) + 1):
            (chapter_dir / f"scene_{scene_id:03d}.md").write_text(f"Recovered chapter {chapter_id} scene {scene_id}.", encoding="utf-8")
            _write_json(chapter_dir / f"scene_{scene_id:03d}.meta.json", {"chapter_id": chapter_id, "scene_id": scene_id, "recovered": True})

    monkeypatch.setattr("bookforge.execution.scoped.run_section_range", _fake_run_section_range)
    redraft_scope(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="redraft_scope", branch_id="recover-two-chapters"),
    )
    assert (branch_root / "draft" / "chapters" / "ch_001" / "scene_001.md").read_text(encoding="utf-8") == "Recovered chapter 1 scene 1."
    assert (branch_root / "draft" / "chapters" / "ch_002" / "scene_001.md").read_text(encoding="utf-8") == "Recovered chapter 2 scene 1."

    validate_result = validate_recovery_branch(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="validate_recovery_branch", branch_id="recover-two-chapters"),
    )
    assert validate_result.status == "success"

    promote_result = promote_recovery_branch(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="promote_recovery_branch", branch_id="recover-two-chapters"),
    )
    assert promote_result.status == "success"
    assert promote_result.details["postcondition"]["post_outline_lineage_status"] == "healthy"
    for chapter_id in (1, 2):
        assert not (book_root / "outline" / "section_drafts" / f"ch_{chapter_id:03d}_sec_001_phase03.json").exists()
        assert not (book_root / "draft" / "chapters" / f"ch_{chapter_id:03d}" / "scene_002.md").exists()
        assert (book_root / "draft" / "chapters" / f"ch_{chapter_id:03d}" / "scene_001.md").read_text(encoding="utf-8") == (
            f"Recovered chapter {chapter_id} scene 1."
        )
    main_index = _read_json(book_root / "draft" / "context" / "characters" / "index.json")
    assert [entry["character_id"] for entry in main_index["characters"]] == ["rhea_mercer", "vance_harrow"]
    assert get_outline_lineage_audit(tmp_path, "my_book").status == "healthy"


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
    assert _postcondition(quarantine_result)["recommended_next_action"] == "normalize_outline_scope"
    assert "normalize_outline_scope" in _postcondition(quarantine_result)["remaining_required_receipts"]
    assert not (branch_root / "outline" / "section_drafts" / "ch_001_sec_001_phase03.json").exists()
    assert (book_root / "outline" / "section_drafts" / "ch_001_sec_001_phase03.json").exists()

    normalize_result = normalize_outline_scope(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="normalize_outline_scope", branch_id="recover-sec1"),
    )
    assert normalize_result.status == "success"
    assert _postcondition(normalize_result)["recommended_next_action"] == "invalidate_scope_outputs"
    branch_outline = _read_json(branch_root / "outline" / "outline.json")
    assert branch_outline["characters"] == [{"character_id": "rhea_mercer", "name": "Rhea Mercer"}]
    assert len(branch_outline["chapters"][0]["sections"][0]["scenes"]) == 1

    preview = get_scope_invalidation_preview(tmp_path, "my_book", branch_id="recover-sec1")
    assert "draft/chapters/ch_001/scene_001.md" in preview["candidate_paths"]
    assert "draft/chapters/ch_001/scene_002.md" in preview["candidate_paths"]
    state_preview = get_state_rebuild_preview(tmp_path, "my_book", branch_id="recover-sec1")
    assert "state.json" in state_preview["candidate_paths"]
    assert "draft/context/characters/artie.state.json" in state_preview["candidate_paths"]
    assert "draft/context/settings/ch_001/scene_001/prose_extracted.setting.json" in state_preview["candidate_paths"]
    blast_radius = get_recovery_blast_radius(tmp_path, "my_book", branch_id="recover-sec1")
    assert blast_radius["families"]["prose"]["candidate_count"] >= 2
    assert blast_radius["families"]["state"]["candidate_count"] >= 2
    assert blast_radius["families"]["projection"]["candidate_count"] >= 1
    assert "series" in blast_radius["families"]
    assert "future_series_scope_rebuild" in blast_radius["families"]["series"]["recommended_actions"]

    invalidate_result = invalidate_scope_outputs(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="invalidate_scope_outputs", branch_id="recover-sec1"),
    )
    assert invalidate_result.status == "success"
    assert _postcondition(invalidate_result)["recommended_next_action"] == "rebuild_state_scope"
    assert not (branch_root / "draft" / "chapters" / "ch_001" / "scene_002.md").exists()
    assert (book_root / "draft" / "chapters" / "ch_001" / "scene_002.md").exists()

    blocked_validate = validate_recovery_branch(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="validate_recovery_branch", branch_id="recover-sec1"),
    )
    assert blocked_validate.status == "integrity_degraded"
    assert "rebuild_state_scope has not completed" in blocked_validate.details["recovery_receipt"]["details"]["blockers"]
    assert _postcondition(blocked_validate)["branch_health_status_after"] == "blocked"
    assert _postcondition(blocked_validate)["recommended_next_action"] == "rebuild_state_scope"

    rebuild_result = rebuild_state_scope(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="rebuild_state_scope", branch_id="recover-sec1"),
    )
    assert rebuild_result.status == "success"
    assert _postcondition(rebuild_result)["recommended_next_action"] == "redraft_scope"
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
    assert _postcondition(blocked_after_rebuild)["recommended_next_action"] == "redraft_scope"

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
    assert _postcondition(redraft_result)["recommended_next_action"] == "validate_recovery_branch"
    assert (branch_root / "draft" / "chapters" / "ch_001" / "scene_001.md").read_text(encoding="utf-8") == "Recovered scene 1."
    assert not (branch_root / "draft" / "chapters" / "ch_001" / "scene_002.md").exists()

    stale_summary_path = branch_root / "draft" / "context" / "chapter_summaries" / "ch_001.json"
    stale_setting_path = branch_root / "draft" / "context" / "settings" / "ch_001" / "scene_001" / "prose_extracted.setting.json"
    stale_appearance_path = branch_root / "draft" / "context" / "appearance" / "ch_001" / "scene_001" / "appearance_projection.json"
    _write_json(stale_summary_path, {"key_events": ["char_artie survived the old timeline."]})
    _write_json(stale_setting_path, {"node": {"branch_id": "main"}, "setting": {"characters": ["char_artie"]}})
    _write_json(stale_appearance_path, {"node": {"branch_id": "main"}, "characters": [{"character_id": "char_artie"}]})
    blocked_stale_projection = validate_recovery_branch(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="validate_recovery_branch", branch_id="recover-sec1"),
    )
    assert blocked_stale_projection.status == "integrity_degraded"
    projection_blockers = blocked_stale_projection.details["recovery_receipt"]["details"]["state_projection_blockers"]
    assert any("chapter summary references non-outline character: char_artie" in blocker for blocker in projection_blockers)
    assert any("setting projection has stale node branch main" in blocker for blocker in projection_blockers)
    assert any("appearance projection references non-outline character: char_artie" in blocker for blocker in projection_blockers)
    stale_summary_path.unlink()
    stale_setting_path.unlink()
    stale_appearance_path.unlink()

    stale_continuity_pack = branch_root / "draft" / "context" / "continuity_pack.json"
    stale_bible_path = branch_root / "draft" / "context" / "bible.md"
    stale_seam_report = branch_root / "draft" / "context" / "chapter_seams" / "ch_001" / "chapter_seam_report.json"
    _write_json(
        stale_continuity_pack,
        {
            "scene_end_anchor": "char_artie escaped the polluted timeline.",
            "constraints": [],
            "open_threads": [],
            "cast_present": ["char_artie"],
            "location": "",
            "next_action": "",
        },
    )
    stale_bible_path.write_text("char_artie remains canonical after the wrong outline pass.\n", encoding="utf-8")
    _write_json(stale_seam_report, {"node": {"branch_id": "main"}, "notes": ["char_artie overlap persists."]})
    blocked_continuity_state = validate_recovery_branch(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="validate_recovery_branch", branch_id="recover-sec1"),
    )
    assert blocked_continuity_state.status == "integrity_degraded"
    continuity_blockers = blocked_continuity_state.details["recovery_receipt"]["details"]["state_projection_blockers"]
    assert any("continuity pack references non-outline character: char_artie" in blocker for blocker in continuity_blockers)
    assert any("world bible references non-outline character: char_artie" in blocker for blocker in continuity_blockers)
    assert any("chapter seam artifact references non-outline character: char_artie" in blocker for blocker in continuity_blockers)
    assert any("chapter seam artifact has stale node branch main" in blocker for blocker in continuity_blockers)
    stale_continuity_pack.unlink()
    stale_bible_path.write_text("", encoding="utf-8")
    stale_seam_report.unlink()

    context_dir = branch_root / "draft" / "context"
    _write_json(
        context_dir / "item_registry.json",
        {
            "schema_version": "1.0",
            "items": [
                {
                    "item_id": "ITEM_wrong",
                    "name": "Polluted Item",
                    "custodian": "char_artie",
                    "linked_threads": [],
                    "last_seen": {"chapter": 1, "scene": 1},
                }
            ],
        },
    )
    _write_json(context_dir / "items" / "index.json", {"schema_version": "1.0", "item_ids": ["ITEM_wrong", "ITEM_missing"]})
    _write_json(
        context_dir / "plot_devices.json",
        {
            "schema_version": "1.0",
            "devices": [
                {
                    "device_id": "DEVICE_wrong",
                    "custody_ref": "char_artie",
                    "linked_threads": [],
                    "last_seen": {"chapter": 1, "scene": 1},
                }
            ],
        },
    )
    _write_json(
        context_dir / "plot_devices" / "index.json",
        {"schema_version": "1.0", "device_ids": ["DEVICE_wrong", "DEVICE_missing"]},
    )
    blocked_durable_state = validate_recovery_branch(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="validate_recovery_branch", branch_id="recover-sec1"),
    )
    assert blocked_durable_state.status == "integrity_degraded"
    durable_blockers = blocked_durable_state.details["recovery_receipt"]["details"]["state_projection_blockers"]
    assert any("item registry references non-outline character: char_artie" in blocker for blocker in durable_blockers)
    assert any("plot device registry references non-outline character: char_artie" in blocker for blocker in durable_blockers)
    assert any("item index references missing registry item: ITEM_missing" in blocker for blocker in durable_blockers)
    assert any("plot device index references missing registry device: DEVICE_missing" in blocker for blocker in durable_blockers)
    _write_json(context_dir / "item_registry.json", {"schema_version": "1.0", "items": []})
    _write_json(context_dir / "items" / "index.json", {"schema_version": "1.0", "item_ids": []})
    _write_json(context_dir / "plot_devices.json", {"schema_version": "1.0", "devices": []})
    _write_json(context_dir / "plot_devices" / "index.json", {"schema_version": "1.0", "device_ids": []})

    rogue_character_dir = branch_root / "draft" / "context" / "characters"
    _write_json(
        rogue_character_dir / "index.json",
        {
            "characters": [
                {"character_id": "rhea_mercer", "state_path": "draft/context/characters/rhea_mercer.state.json"},
                {"character_id": "char_artie", "state_path": "draft/context/characters/artie.state.json"},
            ]
        },
    )
    _write_json(rogue_character_dir / "artie.state.json", {"character_id": "char_artie", "name": "Artie"})
    blocked_ghost_state = validate_recovery_branch(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="validate_recovery_branch", branch_id="recover-sec1"),
    )
    assert blocked_ghost_state.status == "integrity_degraded"
    ghost_blockers = blocked_ghost_state.details["recovery_receipt"]["details"]["state_projection_blockers"]
    assert any("non-outline character: char_artie" in blocker for blocker in ghost_blockers)
    _write_json(
        rogue_character_dir / "index.json",
        {"characters": [{"character_id": "rhea_mercer", "state_path": "draft/context/characters/rhea_mercer.state.json"}]},
    )
    (rogue_character_dir / "artie.state.json").unlink()

    validate_result = validate_recovery_branch(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="validate_recovery_branch", branch_id="recover-sec1"),
    )
    assert validate_result.status == "success"
    validate_postcondition = _postcondition(validate_result)
    semantic_validation = validate_result.details["recovery_receipt"]["details"]["semantic_validation"]
    assert semantic_validation["status"] == "deferred"
    assert "semantic_continuity" in semantic_validation["families"]
    validation_manifest = get_recovery_manifest(tmp_path, "my_book", branch_id="recover-sec1")
    assert validation_manifest["validation"]["semantic_validation"]["status"] == "deferred"
    assert validate_postcondition["branch_health_status_after"] == "healthy"
    assert validate_postcondition["remaining_required_receipts"] == []
    assert validate_postcondition["recommended_next_action"] == "promote_recovery_branch"
    assert validate_postcondition["canonical_change_status"] == "none"
    health = get_recovery_branch_health(tmp_path, "my_book", branch_id="recover-sec1")
    assert health.status == "healthy"
    assert health.details["recommended_next_action"] == "promote_recovery_branch"
    assert "promotion to main" in health.details["approval_reasons"]
    assert health.details["semantic_validation"]["status"] == "deferred"
    semantic_readiness = get_recovery_semantic_review_readiness(tmp_path, "my_book", branch_id="recover-sec1")
    assert semantic_readiness["ready"] is True
    assert semantic_readiness["status"] == "ready"
    assert semantic_readiness["artifact_status"] == "diagnostic"
    assert semantic_readiness["mutation_scope"] == "diagnostic_only"
    assert semantic_readiness["structural_health_status"] == "healthy"
    assert semantic_readiness["semantic_validation_status"] == "deferred"
    assert semantic_readiness["recommended_next_action"] == "review_recovery_semantics"
    semantic_review = get_recovery_semantic_review(tmp_path, "my_book", branch_id="recover-sec1")
    assert semantic_review["status"] == "not_started"
    assert semantic_review["artifact_status"] == "diagnostic"
    assert semantic_review["readiness"]["ready"] is True
    assert semantic_review["blocked_actions"] == []
    assert semantic_review["recommended_next_action"] == "review_recovery_semantics"
    branch_selector = ScopeSelector(book_id="my_book", branch_id="recover-sec1", chapter=1, section=1)
    branch_actions = {option.action: option for option in list_execution_options(tmp_path, branch_selector, prefer_emitted=False)}
    assert branch_actions["review_recovery_semantics"].allowed is True
    assert branch_actions["review_downstream_dependencies"].allowed is True
    downstream_result = review_downstream_dependencies(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="review_downstream_dependencies", branch_id="recover-sec1"),
    )
    assert downstream_result.status == "success"
    downstream_review = get_downstream_dependency_review(tmp_path, "my_book", branch_id="recover-sec1")
    assert downstream_review["status"] == "reviewed_clean"
    assert downstream_review["artifact_status"] == "diagnostic"
    assert downstream_review["readiness"]["ready"] is True
    health_after_downstream = get_recovery_branch_health(tmp_path, "my_book", branch_id="recover-sec1")
    assert health_after_downstream.details["downstream_dependency_review"]["status"] == "reviewed_clean"
    review_result = review_recovery_semantics(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="review_recovery_semantics", branch_id="recover-sec1"),
    )
    assert review_result.status == "success"
    emitted_review = get_recovery_semantic_review(tmp_path, "my_book", branch_id="recover-sec1")
    assert emitted_review["status"] == "reviewed_attention_required"
    assert emitted_review["artifact_status"] == "diagnostic"
    assert any(finding["category"] == "semantic_continuity_risk" for finding in emitted_review["findings"])
    assert emitted_review["readiness"]["present_outputs"][0]["artifact_status"] == "diagnostic"
    health_after_review = get_recovery_branch_health(tmp_path, "my_book", branch_id="recover-sec1")
    assert health_after_review.details["semantic_validation"]["status"] == "reviewed_attention_required"

    promote_result = promote_recovery_branch(
        tmp_path,
        build_recovery_branch_request(tmp_path, "my_book", action="promote_recovery_branch", branch_id="recover-sec1"),
    )
    assert promote_result.status == "success"
    promotion_postcondition = promote_result.details["postcondition"]
    assert promotion_postcondition["canonical_change_status"] == "canonical"
    assert promotion_postcondition["pre_outline_lineage_status"] == "chimera_risk"
    assert promotion_postcondition["post_outline_lineage_status"] == "healthy"
    assert promotion_postcondition["main_recovered_from_chimera"] is True
    assert "outline/section_drafts/ch_001_sec_001_phase03.json" in promotion_postcondition["applied_removed_paths"]
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
        "recovery-blast-radius",
        "rebuild-state-scope",
        "redraft-scope",
        "validate-recovery-branch",
        "review-downstream-dependencies",
        "review-recovery-semantics",
        "promote-recovery-branch",
        "recovery-health",
        "recovery-readiness",
        "recovery-semantic-readiness",
        "recovery-semantic-review",
        "downstream-dependency-review",
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
