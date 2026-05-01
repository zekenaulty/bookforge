from __future__ import annotations

import json
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from bookforge.contracts import (
    ExecutionRequest,
    ExecutionResult,
    MAIN_BRANCH_ID,
    ProducedArtifactReceipt,
    ScopeSelector,
    TimelineNodeRef,
    VisualPromptPlan,
)
from bookforge.query.visual import DEFAULT_VISUAL_MODEL, resolve_visual_provider
from bookforge.visual.providers import GeneratedImage, generate_image_from_prompt


VISUAL_SOURCE_RUN_ID = "visual_assets"


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


def _node(*, book_id: str, branch_id: str, revision_id: str, phase_id: str) -> TimelineNodeRef:
    return TimelineNodeRef(
        book_id=book_id,
        workflow_family="visual_assets",
        source_run_id=VISUAL_SOURCE_RUN_ID,
        branch_id=branch_id,
        phase_id=phase_id,
        revision_id=revision_id,
    )


def _visual_root(workspace: Path, book_id: str, branch_id: str) -> Path:
    if branch_id == MAIN_BRANCH_ID:
        return workspace / "books" / book_id / "visual"
    return workspace / "books" / book_id / "runtime" / "supervision" / "branches" / branch_id / "visual"


def _ensure_visual_scope(workspace: Path, book_id: str, branch_id: str) -> None:
    book_root = workspace / "books" / book_id
    if not book_root.exists():
        raise FileNotFoundError(f"Book workspace not found: {book_id}")
    if branch_id == MAIN_BRANCH_ID:
        return
    branch_manifest = book_root / "runtime" / "supervision" / "branches" / branch_id / "branch_manifest.json"
    legacy_manifest = book_root / "runtime" / "branches" / branch_id / "branch_manifest.json"
    if not branch_manifest.exists() and not legacy_manifest.exists():
        raise FileNotFoundError(f"Branch workspace not found for visual asset action: {branch_id}")


def _prompt_plan_id() -> str:
    return f"visual_prompt_plan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _provider_prompt(
    *,
    visual_purpose: str,
    user_prompt: str,
    style_profile: Optional[str],
    layer_intent: Optional[str],
    provider_model: str,
) -> str:
    purpose_lines = {
        "background_layer": "Create a background/environment plate. No text, no logos, no foreground character focus.",
        "character_reference": "Create a character reference image. Preserve identity cues and readable silhouette.",
        "character_in_scene": "Create a character-in-scene image. Preserve character identity while matching the scene environment.",
        "transparent_foreground_layer": "Create a foreground layer intended for compositing. Use transparent background only if the provider supports alpha.",
        "scene_illustration": "Create a polished scene illustration that captures the prose moment and emotional tone.",
        "style_transfer": "Refine or restyle the source image while preserving the requested subject constraints.",
    }
    lines = [
        purpose_lines.get(visual_purpose, f"Create a visual asset for purpose: {visual_purpose}."),
        f"Provider target: {provider_model}.",
    ]
    if style_profile:
        lines.append(f"Style profile: {style_profile.strip()}")
    if layer_intent:
        lines.append(f"Layer/composition intent: {layer_intent.strip()}")
    lines.append("User visual brief:")
    lines.append(user_prompt.strip())
    lines.append("Avoid text artifacts unless explicitly requested. Keep visual continuity constraints concrete.")
    return "\n".join(lines)


def build_plan_visual_asset_request(
    *,
    book_id: str,
    prompt_text: str,
    visual_purpose: str = "background_layer",
    provider_model: Optional[str] = None,
    branch_id: Optional[str] = None,
    style_profile: Optional[str] = None,
    layer_intent: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    request_id: Optional[str] = None,
) -> ExecutionRequest:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    return ExecutionRequest(
        request_id=request_id or _request_id("plan_visual_asset"),
        action="plan_visual_asset",
        selector=ScopeSelector(book_id=_clean_required(book_id, "book_id"), branch_id=resolved_branch_id, workflow_family="visual_assets"),
        requested_at=_utc_now(),
        details={
            "prompt_text": _clean_required(prompt_text, "prompt_text"),
            "visual_purpose": _clean_required(visual_purpose, "visual_purpose"),
            "provider_model": _clean_optional(provider_model) or DEFAULT_VISUAL_MODEL,
            "style_profile": _clean_optional(style_profile),
            "layer_intent": _clean_optional(layer_intent),
            "negative_prompt": _clean_optional(negative_prompt),
        },
    )


def build_generate_visual_asset_request(
    *,
    book_id: str,
    prompt_plan_path: Path | str,
    branch_id: Optional[str] = None,
    provider_model: Optional[str] = None,
    allow_spend: bool = False,
    request_id: Optional[str] = None,
) -> ExecutionRequest:
    resolved_branch_id = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    return ExecutionRequest(
        request_id=request_id or _request_id("generate_visual_asset"),
        action="generate_visual_asset",
        selector=ScopeSelector(book_id=_clean_required(book_id, "book_id"), branch_id=resolved_branch_id, workflow_family="visual_assets"),
        requested_at=_utc_now(),
        details={
            "prompt_plan_path": _clean_required(prompt_plan_path, "prompt_plan_path"),
            "provider_model": _clean_optional(provider_model),
            "allow_spend": bool(allow_spend),
        },
    )


def plan_visual_asset_action(workspace: Path, request: ExecutionRequest) -> ExecutionResult:
    if request.action != "plan_visual_asset":
        raise ValueError("Unsupported execution action.")
    details = dict(request.details or {})
    provider = resolve_visual_provider(details.get("provider_model"))
    book_id = request.selector.book_id
    branch_id = request.selector.branch_id or MAIN_BRANCH_ID
    workspace_path = Path(workspace)
    _ensure_visual_scope(workspace_path, book_id, branch_id)
    plan_id = _prompt_plan_id()
    visual_purpose = _clean_required(details.get("visual_purpose"), "visual_purpose")
    user_prompt = _clean_required(details.get("prompt_text"), "prompt_text")
    prompt_plan = VisualPromptPlan(
        prompt_plan_id=plan_id,
        visual_purpose=visual_purpose,
        provider_id=provider.provider_id,
        model_id=provider.model_id,
        user_prompt=user_prompt,
        provider_prompt=_provider_prompt(
            visual_purpose=visual_purpose,
            user_prompt=user_prompt,
            style_profile=_clean_optional(details.get("style_profile")),
            layer_intent=_clean_optional(details.get("layer_intent")),
            provider_model=provider.model_id,
        ),
        negative_prompt=_clean_optional(details.get("negative_prompt")),
        style_profile=_clean_optional(details.get("style_profile")),
        layer_intent=_clean_optional(details.get("layer_intent")),
        details={
            "provider_key": provider.key,
            "provider_display_name": provider.display_name,
            "provider_implementation_status": provider.implementation_status,
            "default_model": DEFAULT_VISUAL_MODEL,
        },
    )
    root = _visual_root(workspace_path, book_id, branch_id)
    plan_dir = root / "prompt_plans"
    plan_dir.mkdir(parents=True, exist_ok=True)
    output_path = plan_dir / f"{plan_id}.json"
    output_path.write_text(json.dumps(prompt_plan.to_dict(), ensure_ascii=True, indent=2), encoding="utf-8")
    rel_path = output_path.as_posix()
    receipt = ProducedArtifactReceipt(
        artifact_key="visual_prompt_plan",
        label="Visual prompt plan",
        artifact_status="provisional",
        path=rel_path,
        format="json",
        consumable=True,
        resumable=False,
        replaceable=True,
        details={
            "visual_purpose": visual_purpose,
            "provider_id": provider.provider_id,
            "model_id": provider.model_id,
        },
    )
    return ExecutionResult(
        result_id=f"{request.request_id}_result",
        action="plan_visual_asset",
        status="success",
        node=_node(book_id=book_id, branch_id=branch_id, revision_id=plan_id, phase_id="plan_visual_asset"),
        selector=request.selector,
        message="Visual prompt plan created.",
        artifact_paths={"visual_prompt_plan": rel_path},
        produced_artifacts=[receipt],
        details={
            "prompt_plan_id": plan_id,
            "visual_purpose": visual_purpose,
            "provider_id": provider.provider_id,
            "model_id": provider.model_id,
            "provider_key": provider.key,
            "default_model": DEFAULT_VISUAL_MODEL,
        },
        emitted_at=_utc_now(),
        request_id=request.request_id,
    )


def _load_prompt_plan(path: Path) -> VisualPromptPlan:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Visual prompt plan must be a JSON object.")
    return VisualPromptPlan(
        prompt_plan_id=payload.get("prompt_plan_id"),
        visual_purpose=payload.get("visual_purpose"),
        provider_id=payload.get("provider_id"),
        model_id=payload.get("model_id"),
        user_prompt=payload.get("user_prompt"),
        provider_prompt=payload.get("provider_prompt"),
        negative_prompt=payload.get("negative_prompt"),
        style_profile=payload.get("style_profile"),
        reference_image_refs=list(payload.get("reference_image_refs") or []),
        layer_intent=payload.get("layer_intent"),
        details=payload.get("details") or {},
        schema_version=str(payload.get("schema_version") or "visual_prompt_plan_v1"),
    )


def _extension_for_mime(mime_type: str) -> str:
    normalized = str(mime_type or "").lower()
    if "jpeg" in normalized or "jpg" in normalized:
        return ".jpg"
    if "webp" in normalized:
        return ".webp"
    return ".png"


def generate_visual_asset_action(
    workspace: Path,
    request: ExecutionRequest,
    *,
    generator=generate_image_from_prompt,
) -> ExecutionResult:
    if request.action != "generate_visual_asset":
        raise ValueError("Unsupported execution action.")
    details = dict(request.details or {})
    if not bool(details.get("allow_spend")):
        raise ValueError("generate_visual_asset requires explicit allow_spend=true.")
    book_id = request.selector.book_id
    branch_id = request.selector.branch_id or MAIN_BRANCH_ID
    workspace_path = Path(workspace)
    _ensure_visual_scope(workspace_path, book_id, branch_id)
    plan_path = Path(_clean_required(details.get("prompt_plan_path"), "prompt_plan_path"))
    if not plan_path.is_absolute():
        plan_path = workspace_path / plan_path
    if not plan_path.exists():
        raise FileNotFoundError(f"Visual prompt plan not found: {plan_path}")
    prompt_plan = _load_prompt_plan(plan_path)
    provider = resolve_visual_provider(details.get("provider_model") or prompt_plan.model_id)
    result: GeneratedImage = generator(provider, prompt_plan.provider_prompt)
    asset_id = f"visual_asset_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    root = _visual_root(workspace_path, book_id, branch_id)
    asset_dir = root / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    ext = _extension_for_mime(result.mime_type)
    image_path = asset_dir / f"{asset_id}{ext}"
    image_path.write_bytes(result.bytes)
    sha256 = hashlib.sha256(result.bytes).hexdigest()
    manifest = {
        "schema_version": "visual_asset_manifest_v1",
        "asset_id": asset_id,
        "book_id": book_id,
        "branch_id": branch_id,
        "provider_id": result.provider_id,
        "model_id": result.model_id,
        "mime_type": result.mime_type,
        "sha256": sha256,
        "prompt_plan_id": prompt_plan.prompt_plan_id,
        "prompt_plan_path": plan_path.as_posix(),
        "image_path": image_path.as_posix(),
        "visual_purpose": prompt_plan.visual_purpose,
        "artifact_status": "provisional",
        "text_parts": list(result.text_parts),
        "usage": dict(result.usage),
        "created_at": _utc_now(),
    }
    manifest_path = asset_dir / f"{asset_id}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2), encoding="utf-8")
    image_receipt = ProducedArtifactReceipt(
        artifact_key="visual_image",
        label="Visual image asset",
        artifact_status="provisional",
        path=image_path.as_posix(),
        format=result.mime_type,
        consumable=True,
        replaceable=True,
        details={"sha256": sha256, "asset_id": asset_id, "visual_purpose": prompt_plan.visual_purpose},
    )
    manifest_receipt = ProducedArtifactReceipt(
        artifact_key="visual_asset_manifest",
        label="Visual asset manifest",
        artifact_status="diagnostic",
        path=manifest_path.as_posix(),
        format="json",
        consumable=True,
        replaceable=True,
        details={"asset_id": asset_id},
    )
    return ExecutionResult(
        result_id=f"{request.request_id}_result",
        action="generate_visual_asset",
        status="success",
        node=_node(book_id=book_id, branch_id=branch_id, revision_id=asset_id, phase_id="generate_visual_asset"),
        selector=request.selector,
        message="Visual asset generated.",
        artifact_paths={"visual_image": image_path.as_posix(), "visual_asset_manifest": manifest_path.as_posix()},
        produced_artifacts=[image_receipt, manifest_receipt],
        details={
            "asset_id": asset_id,
            "sha256": sha256,
            "provider_id": result.provider_id,
            "model_id": result.model_id,
            "mime_type": result.mime_type,
            "prompt_plan_id": prompt_plan.prompt_plan_id,
            "visual_purpose": prompt_plan.visual_purpose,
        },
        emitted_at=_utc_now(),
        request_id=request.request_id,
    )
