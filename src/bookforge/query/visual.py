from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from bookforge.contracts import MAIN_BRANCH_ID, ScopeSelector, VisualActionReadiness, VisualProviderDescriptor


DEFAULT_VISUAL_MODEL = "nano-banana"
_VERIFIED_ON = "2026-04-28"

_STANDARD_PURPOSES = [
    "background_layer",
    "character_reference",
    "character_in_scene",
    "scene_illustration",
    "style_transfer",
]


def _descriptor(
    *,
    provider_id: str,
    model_id: str,
    display_name: str,
    implementation_status: str,
    aliases: Iterable[str] = (),
    purposes: Iterable[str] = _STANDARD_PURPOSES,
    ratios: Iterable[str] = ("1:1", "16:9", "9:16", "4:3", "3:4"),
    formats: Iterable[str] = ("png",),
    edit: bool = False,
    refs: bool = False,
    alpha: bool = False,
    max_refs: Optional[int] = None,
    default_for: Iterable[str] = (),
    price_notes: Optional[str] = None,
    price_verified: bool = True,
    sources: Iterable[str] = (),
    limitations: Iterable[str] = (),
    details: Optional[dict] = None,
) -> VisualProviderDescriptor:
    return VisualProviderDescriptor(
        provider_id=provider_id,
        model_id=model_id,
        display_name=display_name,
        implementation_status=implementation_status,
        aliases=list(aliases),
        supported_purposes=list(purposes),
        supported_aspect_ratios=list(ratios),
        output_formats=list(formats),
        generation_supported=True,
        edit_supported=edit,
        reference_image_supported=refs,
        transparent_background_supported=alpha,
        max_reference_images=max_refs,
        default_for_purpose=list(default_for),
        price_notes=price_notes,
        price_verified=price_verified,
        verification_date=_VERIFIED_ON,
        source_urls=list(sources),
        limitations=list(limitations),
        details=dict(details or {}),
    )


_PROVIDERS: List[VisualProviderDescriptor] = [
    _descriptor(
        provider_id="google",
        model_id="gemini-2.5-flash-image",
        display_name="Google Nano Banana / Gemini 2.5 Flash Image",
        implementation_status="adapter_ready",
        aliases=["nano-banana", "gemini-2.5-flash-image"],
        refs=True,
        max_refs=3,
        default_for=_STANDARD_PURPOSES,
        price_notes="Standard output listed around $0.039/image up to 1024x1024; batch/flex lower.",
        sources=[
            "https://ai.google.dev/gemini-api/docs/image-generation",
            "https://ai.google.dev/gemini-api/docs/pricing",
        ],
        limitations=[
            "Live adapter uses the Gemini generateContent REST API and requires GEMINI_API_KEY or GOOGLE_API_KEY.",
            "Preview/model naming may change; descriptor carries verification date.",
        ],
        details={"default_route": True},
    ),
    _descriptor(
        provider_id="openai",
        model_id="gpt-image-2",
        display_name="OpenAI GPT Image 2",
        implementation_status="adapter_ready",
        aliases=["image-2", "gpt-image-2", "openai-image-2"],
        purposes=["background_layer", "character_reference", "character_in_scene", "scene_illustration", "style_transfer"],
        ratios=("1:1", "16:9", "9:16", "4:3", "3:4"),
        edit=True,
        refs=True,
        alpha=False,
        max_refs=16,
        price_notes="Image output listed at $30/1M tokens; price varies by quality/size.",
        sources=[
            "https://developers.openai.com/api/docs/pricing",
            "https://developers.openai.com/api/docs/guides/image-generation",
        ],
        limitations=[
            "Live adapter uses the OpenAI /v1/images/generations endpoint and requires OPENAI_API_KEY or OPENAI_KEY.",
            "OpenAI docs reviewed for this plan state gpt-image-2 does not support transparent backgrounds.",
            "Text rendering, precise composition, and recurring character consistency can fail.",
        ],
    ),
    _descriptor(
        provider_id="openai",
        model_id="dall-e-3",
        display_name="OpenAI DALL-E 3",
        implementation_status="legacy_descriptor",
        aliases=["dall-e-3", "dalle-3"],
        purposes=["background_layer", "scene_illustration"],
        edit=False,
        refs=False,
        alpha=False,
        price_notes="Standard listed at $0.04 square / $0.08 non-square; HD higher.",
        sources=["https://developers.openai.com/api/docs/models/dall-e-3"],
        limitations=[
            "Use as optional scenic/backdrop ideation, not precision reference/layer work.",
            "Previous-generation/legacy route.",
        ],
    ),
    _descriptor(
        provider_id="xai",
        model_id="grok-imagine-image",
        display_name="xAI Grok Imagine",
        implementation_status="experimental_descriptor",
        aliases=["grok", "grok-imagine-image", "xai-imagine"],
        edit=True,
        refs=True,
        alpha=False,
        max_refs=1,
        price_notes="Official docs reviewed did not expose a concrete public image price.",
        price_verified=False,
        sources=[
            "https://docs.x.ai/developers/model-capabilities/images/generation",
            "https://docs.x.ai/developers/models",
        ],
        limitations=[
            "Treat as experimental until account-level pricing and live output behavior are verified.",
        ],
    ),
]


@dataclass(frozen=True, slots=True)
class VisualPromptPlanRecord:
    prompt_plan_id: str
    book_id: str
    branch_id: str
    visual_purpose: str
    provider_id: str
    model_id: str
    path: str
    artifact_status: str
    created_at: Optional[str]
    user_prompt_preview: str
    details: Dict[str, Any]
    schema_version: str = "visual_prompt_plan_record_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "prompt_plan_id": self.prompt_plan_id,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "visual_purpose": self.visual_purpose,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "path": self.path,
            "artifact_status": self.artifact_status,
            "created_at": self.created_at,
            "user_prompt_preview": self.user_prompt_preview,
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class VisualAssetRecord:
    asset_id: str
    book_id: str
    branch_id: str
    visual_purpose: str
    provider_id: str
    model_id: str
    image_path: str
    manifest_path: str
    prompt_plan_id: Optional[str]
    prompt_plan_path: Optional[str]
    mime_type: Optional[str]
    sha256: Optional[str]
    artifact_status: str
    created_at: Optional[str]
    details: Dict[str, Any]
    schema_version: str = "visual_asset_record_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "asset_id": self.asset_id,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "visual_purpose": self.visual_purpose,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "image_path": self.image_path,
            "manifest_path": self.manifest_path,
            "prompt_plan_id": self.prompt_plan_id,
            "prompt_plan_path": self.prompt_plan_path,
            "mime_type": self.mime_type,
            "sha256": self.sha256,
            "artifact_status": self.artifact_status,
            "created_at": self.created_at,
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class VisualAssetIndex:
    book_id: str
    branch_id: str
    selector: ScopeSelector
    prompt_plans: List[VisualPromptPlanRecord]
    assets: List[VisualAssetRecord]
    warnings: List[str]
    source: str = "bookforge.query.visual.v1"
    schema_version: str = "visual_asset_index_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "selector": self.selector.to_dict(),
            "source": self.source,
            "prompt_plan_count": len(self.prompt_plans),
            "asset_count": len(self.assets),
            "prompt_plans": [item.to_dict() for item in self.prompt_plans],
            "assets": [item.to_dict() for item in self.assets],
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class VisualPromptPlanDetail:
    book_id: str
    branch_id: str
    selector: ScopeSelector
    prompt_plan: VisualPromptPlanRecord
    payload: Dict[str, Any]
    source: str = "bookforge.query.visual.v1"
    schema_version: str = "visual_prompt_plan_detail_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "selector": self.selector.to_dict(),
            "source": self.source,
            "prompt_plan": self.prompt_plan.to_dict(),
            "payload": dict(self.payload),
        }


@dataclass(frozen=True, slots=True)
class VisualAssetDetail:
    book_id: str
    branch_id: str
    selector: ScopeSelector
    asset: VisualAssetRecord
    manifest: Dict[str, Any]
    prompt_plan: Optional[VisualPromptPlanRecord]
    prompt_plan_payload: Optional[Dict[str, Any]]
    source: str = "bookforge.query.visual.v1"
    schema_version: str = "visual_asset_detail_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "branch_id": self.branch_id,
            "selector": self.selector.to_dict(),
            "source": self.source,
            "asset": self.asset.to_dict(),
            "manifest": dict(self.manifest),
            "prompt_plan": self.prompt_plan.to_dict() if self.prompt_plan else None,
            "prompt_plan_payload": dict(self.prompt_plan_payload) if isinstance(self.prompt_plan_payload, dict) else None,
        }


def list_visual_provider_descriptors() -> List[VisualProviderDescriptor]:
    return list(_PROVIDERS)


def resolve_visual_provider(model: Optional[str] = None) -> VisualProviderDescriptor:
    requested = str(model or DEFAULT_VISUAL_MODEL).strip().lower()
    for descriptor in _PROVIDERS:
        keys = {descriptor.model_id.lower(), descriptor.key.lower(), *[alias.lower() for alias in descriptor.aliases]}
        if requested in keys:
            return descriptor
    raise ValueError(f"Unknown visual provider/model: {model or DEFAULT_VISUAL_MODEL}")


def _credential_name(provider_id: str) -> str:
    if provider_id == "google":
        return "GEMINI_API_KEY or GOOGLE_API_KEY"
    if provider_id == "openai":
        return "OPENAI_API_KEY or OPENAI_KEY"
    if provider_id == "xai":
        return "XAI_API_KEY"
    return f"{provider_id.upper()}_API_KEY"


def _has_credentials(provider_id: str) -> bool:
    if provider_id == "google":
        return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    if provider_id == "openai":
        return bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY"))
    if provider_id == "xai":
        return bool(os.environ.get("XAI_API_KEY"))
    return False


def _visual_root(workspace: Path, book_id: str, branch_id: str) -> Path:
    resolved_branch = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    if resolved_branch == MAIN_BRANCH_ID:
        return workspace / "books" / book_id / "visual"
    return workspace / "books" / book_id / "runtime" / "supervision" / "branches" / resolved_branch / "visual"


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _mtime_iso(path: Path) -> Optional[str]:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    except OSError:
        return None


def _preview(text: Any, limit: int = 180) -> str:
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(0, limit - 3)].rstrip() + "..."


def _prompt_record(path: Path, payload: Dict[str, Any], *, book_id: str, branch_id: str) -> VisualPromptPlanRecord:
    details = payload.get("details") if isinstance(payload.get("details"), dict) else {}
    return VisualPromptPlanRecord(
        prompt_plan_id=str(payload.get("prompt_plan_id") or path.stem),
        book_id=book_id,
        branch_id=branch_id,
        visual_purpose=str(payload.get("visual_purpose") or "unknown"),
        provider_id=str(payload.get("provider_id") or ""),
        model_id=str(payload.get("model_id") or ""),
        path=path.as_posix(),
        artifact_status=str(payload.get("artifact_status") or "provisional"),
        created_at=str(payload.get("created_at") or "") or _mtime_iso(path),
        user_prompt_preview=_preview(payload.get("user_prompt")),
        details=details,
    )


def _asset_record(path: Path, payload: Dict[str, Any], *, book_id: str, branch_id: str) -> VisualAssetRecord:
    return VisualAssetRecord(
        asset_id=str(payload.get("asset_id") or path.stem.replace(".manifest", "")),
        book_id=str(payload.get("book_id") or book_id),
        branch_id=str(payload.get("branch_id") or branch_id),
        visual_purpose=str(payload.get("visual_purpose") or "unknown"),
        provider_id=str(payload.get("provider_id") or ""),
        model_id=str(payload.get("model_id") or ""),
        image_path=str(payload.get("image_path") or ""),
        manifest_path=path.as_posix(),
        prompt_plan_id=str(payload.get("prompt_plan_id") or "") or None,
        prompt_plan_path=str(payload.get("prompt_plan_path") or "") or None,
        mime_type=str(payload.get("mime_type") or "") or None,
        sha256=str(payload.get("sha256") or "") or None,
        artifact_status=str(payload.get("artifact_status") or "provisional"),
        created_at=str(payload.get("created_at") or "") or _mtime_iso(path),
        details={
            "text_parts": list(payload.get("text_parts") or []),
            "usage": dict(payload.get("usage") or {}) if isinstance(payload.get("usage"), dict) else {},
        },
    )


def _book_exists(workspace: Path, book_id: str) -> bool:
    return (workspace / "books" / book_id / "book.json").exists() or (workspace / "books" / book_id).exists()


def get_visual_asset_index(
    workspace: Path | str,
    book_id: str,
    *,
    branch_id: str = MAIN_BRANCH_ID,
) -> VisualAssetIndex:
    workspace_path = Path(workspace)
    if not _book_exists(workspace_path, book_id):
        raise FileNotFoundError(f"Book workspace not found: {book_id}")
    resolved_branch = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    root = _visual_root(workspace_path, book_id, resolved_branch)
    warnings: List[str] = []
    prompt_records: List[VisualPromptPlanRecord] = []
    asset_records: List[VisualAssetRecord] = []
    prompt_dir = root / "prompt_plans"
    if prompt_dir.exists():
        for path in sorted(prompt_dir.glob("*.json")):
            payload = _read_json(path)
            if payload is None:
                warnings.append(f"Unreadable visual prompt plan: {path.as_posix()}")
                continue
            prompt_records.append(_prompt_record(path, payload, book_id=book_id, branch_id=resolved_branch))
    asset_dir = root / "assets"
    if asset_dir.exists():
        for path in sorted(asset_dir.glob("*.manifest.json")):
            payload = _read_json(path)
            if payload is None:
                warnings.append(f"Unreadable visual asset manifest: {path.as_posix()}")
                continue
            asset_records.append(_asset_record(path, payload, book_id=book_id, branch_id=resolved_branch))
    return VisualAssetIndex(
        book_id=book_id,
        branch_id=resolved_branch,
        selector=ScopeSelector(book_id=book_id, branch_id=resolved_branch, workflow_family="visual_assets"),
        prompt_plans=prompt_records,
        assets=asset_records,
        warnings=warnings,
    )


def _resolve_prompt_plan_path(root: Path, prompt_plan_ref: str) -> Path:
    ref = str(prompt_plan_ref or "").strip()
    if not ref:
        raise ValueError("prompt_plan_ref is required.")
    candidate = Path(ref)
    if candidate.exists():
        return candidate
    if candidate.is_absolute():
        return candidate
    by_id = root / "prompt_plans" / f"{ref}.json"
    if by_id.exists():
        return by_id
    by_name = root / "prompt_plans" / ref
    if by_name.exists():
        return by_name
    return by_id


def get_visual_prompt_plan_detail(
    workspace: Path | str,
    book_id: str,
    prompt_plan_ref: str,
    *,
    branch_id: str = MAIN_BRANCH_ID,
) -> VisualPromptPlanDetail:
    workspace_path = Path(workspace)
    resolved_branch = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    root = _visual_root(workspace_path, book_id, resolved_branch)
    path = _resolve_prompt_plan_path(root, prompt_plan_ref)
    payload = _read_json(path)
    if payload is None:
        raise FileNotFoundError(f"Visual prompt plan not found or unreadable: {prompt_plan_ref}")
    record = _prompt_record(path, payload, book_id=book_id, branch_id=resolved_branch)
    return VisualPromptPlanDetail(
        book_id=book_id,
        branch_id=resolved_branch,
        selector=ScopeSelector(book_id=book_id, branch_id=resolved_branch, workflow_family="visual_assets"),
        prompt_plan=record,
        payload=payload,
    )


def get_visual_asset_detail(
    workspace: Path | str,
    book_id: str,
    asset_id: str,
    *,
    branch_id: str = MAIN_BRANCH_ID,
) -> VisualAssetDetail:
    workspace_path = Path(workspace)
    resolved_branch = str(branch_id or MAIN_BRANCH_ID).strip() or MAIN_BRANCH_ID
    root = _visual_root(workspace_path, book_id, resolved_branch)
    manifest_path = root / "assets" / f"{str(asset_id).strip()}.manifest.json"
    manifest = _read_json(manifest_path)
    if manifest is None:
        raise FileNotFoundError(f"Visual asset manifest not found or unreadable: {asset_id}")
    asset = _asset_record(manifest_path, manifest, book_id=book_id, branch_id=resolved_branch)
    prompt_record = None
    prompt_payload = None
    if asset.prompt_plan_id or asset.prompt_plan_path:
        try:
            detail = get_visual_prompt_plan_detail(
                workspace_path,
                book_id,
                asset.prompt_plan_path or asset.prompt_plan_id or "",
                branch_id=resolved_branch,
            )
            prompt_record = detail.prompt_plan
            prompt_payload = detail.payload
        except (FileNotFoundError, ValueError):
            prompt_record = None
            prompt_payload = None
    return VisualAssetDetail(
        book_id=book_id,
        branch_id=resolved_branch,
        selector=ScopeSelector(book_id=book_id, branch_id=resolved_branch, workflow_family="visual_assets"),
        asset=asset,
        manifest=manifest,
        prompt_plan=prompt_record,
        prompt_plan_payload=prompt_payload,
    )


def get_visual_action_readiness(
    workspace: Path | str,
    *,
    book_id: Optional[str] = None,
    action: str = "generate_background_layer",
    visual_purpose: str = "background_layer",
    provider_model: Optional[str] = None,
    require_credentials: bool = True,
    reference_image_count: int = 0,
    transparent_background: bool = False,
) -> VisualActionReadiness:
    del workspace
    descriptor = resolve_visual_provider(provider_model)
    action_key = str(action or "").strip() or "generate_background_layer"
    missing: List[str] = []
    refusals: List[str] = []
    if visual_purpose not in descriptor.supported_purposes:
        refusals.append("unsupported_visual_purpose")
    if transparent_background and not descriptor.transparent_background_supported:
        refusals.append("unsupported_transparent_background")
    if reference_image_count > 0 and not descriptor.reference_image_supported:
        refusals.append("unsupported_reference_images")
    if descriptor.max_reference_images is not None and reference_image_count > descriptor.max_reference_images:
        refusals.append("too_many_reference_images")
    if require_credentials and action_key != "plan_visual_asset" and not _has_credentials(descriptor.provider_id):
        missing.append(_credential_name(descriptor.provider_id))
    if book_id is None and action not in {"plan_visual_asset"}:
        missing.append("book_id")
    adapter_ready = descriptor.implementation_status == "adapter_ready"
    if action_key == "plan_visual_asset":
        adapter_ready = True
    elif not adapter_ready:
        refusals.append("provider_adapter_missing")
    ready = not missing and not refusals and adapter_ready
    return VisualActionReadiness(
        action=action_key,
        visual_purpose=visual_purpose,
        provider_id=descriptor.provider_id,
        model_id=descriptor.model_id,
        ready=ready,
        allowed=not refusals,
        missing_prerequisites=missing,
        refusal_reasons=refusals,
        produced_artifact_statuses=["provisional"],
        provider=descriptor,
        details={
            "default_model": DEFAULT_VISUAL_MODEL,
            "selected_model": provider_model or DEFAULT_VISUAL_MODEL,
            "requires_credentials": bool(require_credentials),
            "book_id": book_id,
            "credential_name": _credential_name(descriptor.provider_id),
        },
    )
