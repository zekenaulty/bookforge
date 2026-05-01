from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import uuid

from bookforge.author import generate_author
from bookforge.contracts import ExecutionRequest, ExecutionResult, MAIN_BRANCH_ID, ProducedArtifactReceipt, ScopeSelector, TimelineNodeRef
from bookforge.query.authors import get_author_profile


AUTHOR_LIBRARY_SCOPE_ID = "__author_library__"
AUTHOR_ASSETS_SOURCE_RUN_ID = "author_library"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _request_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _clean_required(value: Any, field_name: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required.")
    return cleaned


def _clean_optional(value: Any) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _read_prompt_file(path_value: Any) -> Optional[str]:
    cleaned = _clean_optional(path_value)
    if not cleaned:
        return None
    return Path(cleaned).read_text(encoding="utf-8")


def _selector() -> ScopeSelector:
    return ScopeSelector(book_id=AUTHOR_LIBRARY_SCOPE_ID, branch_id=MAIN_BRANCH_ID, workflow_family="author_assets")


def _node(*, revision_id: str, phase_id: str) -> TimelineNodeRef:
    return TimelineNodeRef(
        book_id=AUTHOR_LIBRARY_SCOPE_ID,
        workflow_family="author_assets",
        source_run_id=AUTHOR_ASSETS_SOURCE_RUN_ID,
        branch_id=MAIN_BRANCH_ID,
        phase_id=phase_id,
        revision_id=revision_id,
    )


def _artifact_path(path: Path) -> str:
    return path.as_posix()


def _artifact_receipts(version_dir: Path) -> list[ProducedArtifactReceipt]:
    return [
        ProducedArtifactReceipt(
            artifact_key="author_json",
            label="Author JSON",
            artifact_status="authoritative",
            path=_artifact_path(version_dir / "author.json"),
            format="json",
            consumable=True,
            replaceable=False,
        ),
        ProducedArtifactReceipt(
            artifact_key="author_style_md",
            label="Author style guide",
            artifact_status="authoritative",
            path=_artifact_path(version_dir / "author_style.md"),
            format="markdown",
            consumable=True,
            replaceable=False,
        ),
        ProducedArtifactReceipt(
            artifact_key="system_fragment_md",
            label="Author system fragment",
            artifact_status="authoritative",
            path=_artifact_path(version_dir / "system_fragment.md"),
            format="markdown",
            consumable=True,
            replaceable=False,
        ),
        ProducedArtifactReceipt(
            artifact_key="author_index",
            label="Author version index",
            artifact_status="authoritative",
            path=_artifact_path(version_dir.parent / "index.json"),
            format="json",
            consumable=True,
            replaceable=True,
        ),
    ]


def _profile_details(workspace: Path, version_dir: Path) -> Dict[str, Any]:
    author_slug = version_dir.parent.name
    version = version_dir.name
    profile = get_author_profile(workspace, f"{author_slug}/{version}")
    return {
        "author_ref": profile.author_ref,
        "author_slug": profile.author_slug,
        "selected_version": profile.selected_version,
        "display_name": profile.display_name,
        "short_description": profile.short_description,
        "artifact_status": profile.artifact_status,
        "version_dir": _artifact_path(version_dir),
    }


def _result(
    *,
    workspace: Path,
    request: ExecutionRequest,
    version_dir: Path,
    action: str,
    phase_id: str,
    message: str,
    extra_details: Optional[Dict[str, Any]] = None,
) -> ExecutionResult:
    details = _profile_details(workspace, version_dir)
    details.update(dict(extra_details or {}))
    artifact_paths = {
        "author_json": _artifact_path(version_dir / "author.json"),
        "author_style_md": _artifact_path(version_dir / "author_style.md"),
        "system_fragment_md": _artifact_path(version_dir / "system_fragment.md"),
        "author_index": _artifact_path(version_dir.parent / "index.json"),
    }
    return ExecutionResult(
        result_id=f"{request.request_id}_result",
        action=action,
        status="success",
        node=_node(revision_id=str(details["selected_version"]), phase_id=phase_id),
        selector=request.selector,
        message=message,
        artifact_paths=artifact_paths,
        produced_artifacts=_artifact_receipts(version_dir),
        details=details,
        emitted_at=_utc_now(),
        request_id=request.request_id,
    )


def _build_refinement_prompt(workspace: Path, author_ref: str, instructions: str) -> str:
    profile = get_author_profile(workspace, author_ref)
    return (
        "Refine this existing BookForge author persona into a new version.\n\n"
        "Preserve the author's core identity, voice center, and recognizable style unless the requested refinement "
        "explicitly asks for a change. Do not overwrite prior versions; create a coherent successor profile.\n\n"
        "Existing author profile:\n"
        f"{profile.profile_markdown}\n\n"
        "Requested refinement:\n"
        f"{instructions.strip()}\n"
    )


def build_create_author_request(
    *,
    name: Optional[str] = None,
    influences: Optional[str] = None,
    prompt_text: Optional[str] = None,
    prompt_file: Optional[Path | str] = None,
    notes: Optional[str] = None,
    request_id: Optional[str] = None,
) -> ExecutionRequest:
    return ExecutionRequest(
        request_id=request_id or _request_id("create_author"),
        action="create_author",
        selector=_selector(),
        requested_at=_utc_now(),
        details={
            "name": _clean_optional(name),
            "influences": _clean_optional(influences),
            "prompt_text": _clean_optional(prompt_text),
            "prompt_file": _clean_optional(prompt_file),
            "notes": _clean_optional(notes),
        },
    )


def build_refine_author_request(
    *,
    author_ref: str,
    instructions: Optional[str] = None,
    prompt_file: Optional[Path | str] = None,
    notes: Optional[str] = None,
    request_id: Optional[str] = None,
) -> ExecutionRequest:
    return ExecutionRequest(
        request_id=request_id or _request_id("refine_author"),
        action="refine_author",
        selector=_selector(),
        requested_at=_utc_now(),
        details={
            "author_ref": _clean_required(author_ref, "author_ref"),
            "instructions": _clean_optional(instructions),
            "prompt_file": _clean_optional(prompt_file),
            "notes": _clean_optional(notes),
        },
    )


def create_author_action(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "create_author":
        raise ValueError("Unsupported execution action.")
    details = dict(request.details or {})
    influences = _clean_optional(details.get("influences"))
    prompt_text = _clean_optional(details.get("prompt_text"))
    prompt_file = Path(details["prompt_file"]) if _clean_optional(details.get("prompt_file")) else None
    if not influences and not prompt_text and not prompt_file:
        raise ValueError("create_author requires influences, prompt_text, or prompt_file.")
    version_dir = generate_author(
        workspace=Path(workspace),
        influences=influences,
        prompt_file=prompt_file,
        name=_clean_optional(details.get("name")),
        notes=_clean_optional(details.get("notes")),
        prompt_text=prompt_text,
    )
    return _result(
        workspace=Path(workspace),
        request=request,
        version_dir=version_dir,
        action="create_author",
        phase_id="create_author",
        message="Author profile created.",
    )


def refine_author_action(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "refine_author":
        raise ValueError("Unsupported execution action.")
    details = dict(request.details or {})
    author_ref = _clean_required(details.get("author_ref"), "author_ref")
    instructions = _clean_optional(details.get("instructions"))
    file_text = _read_prompt_file(details.get("prompt_file"))
    combined_instructions = "\n\n".join(part for part in [instructions, file_text] if part)
    if not combined_instructions:
        raise ValueError("refine_author requires instructions or prompt_file.")
    current_profile = get_author_profile(Path(workspace), author_ref)
    prompt_text = _build_refinement_prompt(Path(workspace), author_ref, combined_instructions)
    version_dir = generate_author(
        workspace=Path(workspace),
        influences=None,
        prompt_file=None,
        name=current_profile.display_name,
        notes=_clean_optional(details.get("notes")) or f"Refinement of {current_profile.author_ref}",
        prompt_text=prompt_text,
    )
    return _result(
        workspace=Path(workspace),
        request=request,
        version_dir=version_dir,
        action="refine_author",
        phase_id="refine_author",
        message="Author profile refined into a new version.",
        extra_details={"source_author_ref": current_profile.author_ref},
    )

