from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import json

from bookforge.contracts import ExecutionRequest, ExecutionResult, MAIN_BRANCH_ID, ProducedArtifactReceipt, ScopeSelector
from bookforge.pipeline.scene_phase_artifacts import load_scene_phase_artifact_state
from bookforge.query import current_execution_node, list_appearance_projection_views

from .scene_actions import (
    _append_execution_result,
    _artifact_relpath,
    _build_execution_node,
    _classify_live_node_mismatch,
    _execution_book_root,
    _hash_id,
    _now_token,
    _request_branch_id,
    _result_for_request,
)


def _scene_setting_dir(book_root: Path, chapter_id: int, scene_id: int) -> Path:
    return book_root / "draft" / "context" / "settings" / f"ch_{chapter_id:03d}" / f"scene_{scene_id:03d}"


def _current_or_committed_prose_path(book_root: Path, chapter_id: int, scene_id: int) -> Optional[Path]:
    artifact_state = load_scene_phase_artifact_state(book_root, chapter_id, scene_id)
    if artifact_state.current_prose_path is not None:
        return artifact_state.current_prose_path
    committed = book_root / "draft" / "chapters" / f"ch_{chapter_id:03d}" / f"scene_{scene_id:03d}.md"
    return committed if committed.exists() else None


def _setting_payload_has_content(payload: Dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    for key in (
        "location_id",
        "location_label",
        "location",
        "background_details",
        "visual_background",
        "setting_details",
        "sensory_anchors",
        "continuity_constraints",
    ):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, list) and value:
            return True
    return False


def _setting_payload_from_request(request: ExecutionRequest, *keys: str) -> Dict[str, Any]:
    for key in keys:
        value = request.details.get(key)
        if isinstance(value, dict):
            return dict(value)
    return {}


def _prose_excerpt(prose: str, *, max_chars: int = 1200) -> str:
    paragraphs = [item.strip() for item in prose.splitlines() if item.strip()]
    text = "\n\n".join(paragraphs[:3]).strip()
    if len(text) > max_chars:
        return text[: max_chars - 3].rstrip() + "..."
    return text


def _base_setting_artifact(
    *,
    request: ExecutionRequest,
    execution_node,
    artifact_status: str,
    source_mode: str,
    setting: Dict[str, Any],
    source_artifacts: list[str],
) -> Dict[str, Any]:
    payload = dict(setting)
    payload.update(
        {
            "schema_version": "scene_setting_projection_artifact_v1",
            "book_id": request.selector.book_id,
            "selector": request.selector.to_dict(),
            "node": execution_node.to_dict(),
            "artifact_status": artifact_status,
            "source_mode": source_mode,
            "source_artifacts": list(source_artifacts),
        }
    )
    return payload


def build_refresh_character_appearance_projection_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
    character_id: Optional[str] = None,
    branch_id: str = MAIN_BRANCH_ID,
) -> ExecutionRequest:
    node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    if node is None:
        raise ValueError(f"No current node is available for refresh_character_appearance_projection on branch {branch_id}.")
    resolved_section = section_id or node.section
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=branch_id,
        workflow_family="section_write",
        chapter=chapter_id,
        section=resolved_section,
        scene=scene_id,
        phase_id="refresh_character_appearance_projection",
    )
    request_seed = "|".join(
        [
            book_id,
            "refresh_character_appearance_projection",
            str(chapter_id),
            str(scene_id),
            str(resolved_section or ""),
            str(character_id or ""),
            branch_id,
            node.revision_id,
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=_hash_id(request_seed),
        action="refresh_character_appearance_projection",
        selector=selector,
        expected_node=node,
        branch_id=branch_id,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "scene_id": int(scene_id),
            "section_id": int(resolved_section) if resolved_section is not None else None,
            "character_id": str(character_id).strip() if character_id else None,
        },
    )


def build_draft_scene_setting_projection_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
    setting: Optional[Dict[str, Any]] = None,
    branch_id: str = MAIN_BRANCH_ID,
) -> ExecutionRequest:
    node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    if node is None:
        raise ValueError(f"No current node is available for draft_scene_setting_projection on branch {branch_id}.")
    resolved_section = section_id or node.section
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=branch_id,
        workflow_family="section_write",
        chapter=chapter_id,
        section=resolved_section,
        scene=scene_id,
        phase_id="draft_scene_setting_projection",
    )
    request_seed = "|".join(
        [
            book_id,
            "draft_scene_setting_projection",
            str(chapter_id),
            str(scene_id),
            str(resolved_section or ""),
            branch_id,
            node.revision_id,
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=_hash_id(request_seed),
        action="draft_scene_setting_projection",
        selector=selector,
        expected_node=node,
        branch_id=branch_id,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "scene_id": int(scene_id),
            "section_id": int(resolved_section) if resolved_section is not None else None,
            "setting": dict(setting or {}),
        },
    )


def build_extract_scene_setting_from_prose_request(
    workspace: Path,
    book_id: str,
    *,
    chapter_id: int,
    scene_id: int,
    section_id: Optional[int] = None,
    extracted_setting: Optional[Dict[str, Any]] = None,
    branch_id: str = MAIN_BRANCH_ID,
) -> ExecutionRequest:
    node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    if node is None:
        raise ValueError(f"No current node is available for extract_scene_setting_from_prose on branch {branch_id}.")
    resolved_section = section_id or node.section
    selector = ScopeSelector(
        book_id=book_id,
        branch_id=branch_id,
        workflow_family="section_write",
        chapter=chapter_id,
        section=resolved_section,
        scene=scene_id,
        phase_id="extract_scene_setting_from_prose",
    )
    request_seed = "|".join(
        [
            book_id,
            "extract_scene_setting_from_prose",
            str(chapter_id),
            str(scene_id),
            str(resolved_section or ""),
            branch_id,
            node.revision_id,
            _now_token(),
        ]
    )
    return ExecutionRequest(
        request_id=_hash_id(request_seed),
        action="extract_scene_setting_from_prose",
        selector=selector,
        expected_node=node,
        branch_id=branch_id,
        requested_at=_now_token(),
        details={
            "chapter_id": int(chapter_id),
            "scene_id": int(scene_id),
            "section_id": int(resolved_section) if resolved_section is not None else None,
            "extracted_setting": dict(extracted_setting or {}),
        },
    )


def refresh_character_appearance_projection(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "refresh_character_appearance_projection":
        raise ValueError("Unsupported execution action.")
    if request.selector.chapter is None or request.selector.scene is None:
        raise ValueError("refresh_character_appearance_projection requires chapter and scene scope.")

    branch_id = _request_branch_id(request)
    book_id = request.selector.book_id
    chapter_id = int(request.selector.chapter)
    scene_id = int(request.selector.scene)
    section_id = int(request.selector.section) if request.selector.section is not None else None
    character_id = str(request.details.get("character_id") or "").strip() or None
    book_root = _execution_book_root(workspace, book_id, branch_id)
    scope_details = {
        "chapter_id": chapter_id,
        "scene_id": scene_id,
        "section_id": section_id,
        "character_id": character_id,
    }

    live_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    if live_node is None:
        selector_node = request.expected_node
        if selector_node is None:
            from bookforge.contracts import TimelineNodeRef

            selector_node = TimelineNodeRef(
                book_id=book_id,
                workflow_family="section_write",
                source_run_id="unknown",
                branch_id=branch_id,
                revision_id="unresolved",
                chapter=chapter_id,
                section=section_id,
                scene=scene_id,
                phase_id="refresh_character_appearance_projection",
            )
        result = _result_for_request(
            request=request,
            node=selector_node,
            status="hard_fail",
            message=f"No live execution node is available for refresh_character_appearance_projection on branch {branch_id}.",
            details={**scope_details, "failure_code": "missing_live_node"},
        )
        _append_execution_result(book_root, result)
        return result

    execution_node = _build_execution_node(
        live_node=live_node,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        phase_id="refresh_character_appearance_projection",
    )
    if request.expected_node is not None and live_node.to_dict() != request.expected_node.to_dict():
        failure_code, message = _classify_live_node_mismatch(
            request.expected_node,
            live_node,
            action="refresh_character_appearance_projection",
        )
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message=message,
            details={
                **scope_details,
                "failure_code": failure_code,
                "expected_node": request.expected_node.to_dict(),
                "live_node": live_node.to_dict(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    views = list_appearance_projection_views(
        workspace,
        book_id,
        branch_id=branch_id,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        character_id=character_id,
        prefer_emitted=False,
    )
    output_dir = book_root / "draft" / "context" / "appearance" / f"ch_{chapter_id:03d}" / f"scene_{scene_id:03d}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "appearance_projection.json"
    payload = {
        "schema_version": "appearance_projection_artifact_v1",
        "book_id": book_id,
        "selector": request.selector.to_dict(),
        "node": execution_node.to_dict(),
        "artifact_status": "derived",
        "character_count": len(views),
        "characters": [view.to_dict() for view in views],
        "limitations": [
            "derived from current character state and outline metadata",
            "does not mutate canonical character truth",
        ],
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    produced = [
        ProducedArtifactReceipt(
            artifact_key="appearance_projection",
            label="Scene character appearance projection",
            artifact_status="derived",
            path=_artifact_relpath(book_root, output_path),
            format="application/json",
            consumable=True,
            resumable=True,
            replaceable=True,
            details={
                **scope_details,
                "character_count": len(views),
                "missing_count": sum(1 for view in views if view.appearance_status == "missing"),
                "stale_count": sum(1 for view in views if view.appearance_status == "stale"),
            },
        )
    ]
    result = _result_for_request(
        request=request,
        node=execution_node,
        status="success",
        message="Derived scene character appearance projection.",
        artifact_paths={item.artifact_key: item.path for item in produced},
        produced_artifacts=produced,
        details={**scope_details, "character_count": len(views)},
    )
    _append_execution_result(book_root, result)
    return result


def draft_scene_setting_projection(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "draft_scene_setting_projection":
        raise ValueError("Unsupported execution action.")
    if request.selector.chapter is None or request.selector.scene is None:
        raise ValueError("draft_scene_setting_projection requires chapter and scene scope.")

    branch_id = _request_branch_id(request)
    book_id = request.selector.book_id
    chapter_id = int(request.selector.chapter)
    scene_id = int(request.selector.scene)
    section_id = int(request.selector.section) if request.selector.section is not None else None
    book_root = _execution_book_root(workspace, book_id, branch_id)
    scope_details = {
        "chapter_id": chapter_id,
        "scene_id": scene_id,
        "section_id": section_id,
    }

    live_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    if live_node is None:
        selector_node = request.expected_node
        if selector_node is None:
            from bookforge.contracts import TimelineNodeRef

            selector_node = TimelineNodeRef(
                book_id=book_id,
                workflow_family="section_write",
                source_run_id="unknown",
                branch_id=branch_id,
                revision_id="unresolved",
                chapter=chapter_id,
                section=section_id,
                scene=scene_id,
                phase_id="draft_scene_setting_projection",
            )
        result = _result_for_request(
            request=request,
            node=selector_node,
            status="hard_fail",
            message=f"No live execution node is available for draft_scene_setting_projection on branch {branch_id}.",
            details={**scope_details, "failure_code": "missing_live_node"},
        )
        _append_execution_result(book_root, result)
        return result

    execution_node = _build_execution_node(
        live_node=live_node,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        phase_id="draft_scene_setting_projection",
    )
    if request.expected_node is not None and live_node.to_dict() != request.expected_node.to_dict():
        failure_code, message = _classify_live_node_mismatch(
            request.expected_node,
            live_node,
            action="draft_scene_setting_projection",
        )
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message=message,
            details={
                **scope_details,
                "failure_code": failure_code,
                "expected_node": request.expected_node.to_dict(),
                "live_node": live_node.to_dict(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    setting = _setting_payload_from_request(request, "setting", "setting_projection")
    if not _setting_payload_has_content(setting):
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="draft_scene_setting_projection requires structured setting details.",
            details={**scope_details, "failure_code": "missing_setting_payload"},
        )
        _append_execution_result(book_root, result)
        return result

    output_dir = _scene_setting_dir(book_root, chapter_id, scene_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "author_drafted.setting.json"
    payload = _base_setting_artifact(
        request=request,
        execution_node=execution_node,
        artifact_status="provisional",
        source_mode="author_drafted",
        setting=setting,
        source_artifacts=[],
    )
    payload["limitations"] = [
        "author-drafted setting intent is provisional",
        "does not mutate canonical scene or location truth",
    ]
    output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    produced = [
        ProducedArtifactReceipt(
            artifact_key="author_drafted_setting_projection",
            label="Author-drafted scene setting projection",
            artifact_status="provisional",
            path=_artifact_relpath(book_root, output_path),
            format="application/json",
            consumable=True,
            resumable=True,
            replaceable=True,
            details={**scope_details, "source_mode": "author_drafted"},
        )
    ]
    result = _result_for_request(
        request=request,
        node=execution_node,
        status="success",
        message="Recorded provisional author-drafted scene setting projection.",
        artifact_paths={item.artifact_key: item.path for item in produced},
        produced_artifacts=produced,
        details={**scope_details, "source_mode": "author_drafted"},
    )
    _append_execution_result(book_root, result)
    return result


def extract_scene_setting_from_prose(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "extract_scene_setting_from_prose":
        raise ValueError("Unsupported execution action.")
    if request.selector.chapter is None or request.selector.scene is None:
        raise ValueError("extract_scene_setting_from_prose requires chapter and scene scope.")

    branch_id = _request_branch_id(request)
    book_id = request.selector.book_id
    chapter_id = int(request.selector.chapter)
    scene_id = int(request.selector.scene)
    section_id = int(request.selector.section) if request.selector.section is not None else None
    book_root = _execution_book_root(workspace, book_id, branch_id)
    scope_details = {
        "chapter_id": chapter_id,
        "scene_id": scene_id,
        "section_id": section_id,
    }

    live_node = current_execution_node(workspace, book_id, branch_id=branch_id, prefer_emitted=False)
    if live_node is None:
        selector_node = request.expected_node
        if selector_node is None:
            from bookforge.contracts import TimelineNodeRef

            selector_node = TimelineNodeRef(
                book_id=book_id,
                workflow_family="section_write",
                source_run_id="unknown",
                branch_id=branch_id,
                revision_id="unresolved",
                chapter=chapter_id,
                section=section_id,
                scene=scene_id,
                phase_id="extract_scene_setting_from_prose",
            )
        result = _result_for_request(
            request=request,
            node=selector_node,
            status="hard_fail",
            message=f"No live execution node is available for extract_scene_setting_from_prose on branch {branch_id}.",
            details={**scope_details, "failure_code": "missing_live_node"},
        )
        _append_execution_result(book_root, result)
        return result

    execution_node = _build_execution_node(
        live_node=live_node,
        chapter_id=chapter_id,
        section_id=section_id,
        scene_id=scene_id,
        phase_id="extract_scene_setting_from_prose",
    )
    if request.expected_node is not None and live_node.to_dict() != request.expected_node.to_dict():
        failure_code, message = _classify_live_node_mismatch(
            request.expected_node,
            live_node,
            action="extract_scene_setting_from_prose",
        )
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message=message,
            details={
                **scope_details,
                "failure_code": failure_code,
                "expected_node": request.expected_node.to_dict(),
                "live_node": live_node.to_dict(),
            },
        )
        _append_execution_result(book_root, result)
        return result

    prose_path = _current_or_committed_prose_path(book_root, chapter_id, scene_id)
    if prose_path is None:
        result = _result_for_request(
            request=request,
            node=execution_node,
            status="hard_fail",
            message="extract_scene_setting_from_prose requires existing scene prose.",
            details={**scope_details, "failure_code": "missing_scene_prose"},
        )
        _append_execution_result(book_root, result)
        return result

    prose = prose_path.read_text(encoding="utf-8")
    setting = _setting_payload_from_request(request, "extracted_setting", "setting")
    if not setting:
        setting = {
            "background_details": [],
            "sensory_anchors": [],
            "continuity_constraints": [],
        }
    setting["source_excerpt"] = _prose_excerpt(prose)

    output_dir = _scene_setting_dir(book_root, chapter_id, scene_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "prose_extracted.setting.json"
    source_rel = _artifact_relpath(book_root, prose_path)
    payload = _base_setting_artifact(
        request=request,
        execution_node=execution_node,
        artifact_status="derived",
        source_mode="prose_extracted",
        setting=setting,
        source_artifacts=[source_rel],
    )
    payload["structured_setting_found"] = _setting_payload_has_content(setting)
    payload["limitations"] = [
        "derived from scene prose, not independently authoritative",
        "does not mutate canonical scene or location truth",
    ]
    output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    produced = [
        ProducedArtifactReceipt(
            artifact_key="prose_extracted_setting_projection",
            label="Prose-extracted scene setting projection",
            artifact_status="derived",
            path=_artifact_relpath(book_root, output_path),
            format="application/json",
            consumable=True,
            resumable=True,
            replaceable=True,
            details={
                **scope_details,
                "source_mode": "prose_extracted",
                "source_prose_path": source_rel,
                "structured_setting_found": _setting_payload_has_content(setting),
            },
        )
    ]
    result = _result_for_request(
        request=request,
        node=execution_node,
        status="success",
        message="Recorded derived scene setting projection from prose.",
        artifact_paths={item.artifact_key: item.path for item in produced},
        produced_artifacts=produced,
        details={
            **scope_details,
            "source_mode": "prose_extracted",
            "source_prose_path": source_rel,
            "structured_setting_found": _setting_payload_has_content(setting),
        },
    )
    _append_execution_result(book_root, result)
    return result
