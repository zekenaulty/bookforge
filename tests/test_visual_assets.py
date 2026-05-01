from __future__ import annotations

import base64
import json
from pathlib import Path

from bookforge.cli import build_parser
from bookforge.contracts import ScopeSelector, VisualActionReadiness, VisualProviderDescriptor
from bookforge.execution import build_plan_visual_asset_request, plan_visual_asset_action
from bookforge.execution import build_generate_visual_asset_request, generate_visual_asset_action
from bookforge.query import (
    get_capability_projection,
    get_visual_asset_detail,
    get_visual_asset_index,
    get_visual_prompt_plan_detail,
    list_execution_options,
)
from bookforge.visual import providers as visual_provider_module
from bookforge.visual.providers import GeneratedImage, generate_image_from_prompt
from bookforge.query.visual import (
    DEFAULT_VISUAL_MODEL,
    get_visual_action_readiness,
    list_visual_provider_descriptors,
    resolve_visual_provider,
)


def test_visual_provider_descriptors_default_to_nano_banana() -> None:
    providers = list_visual_provider_descriptors()
    by_alias = {alias: provider for provider in providers for alias in provider.aliases}

    assert DEFAULT_VISUAL_MODEL == "nano-banana"
    assert by_alias["nano-banana"].provider_id == "google"
    assert by_alias["nano-banana"].model_id == "gemini-2.5-flash-image"
    assert by_alias["image-2"].model_id == "gpt-image-2"
    assert by_alias["image-2"].transparent_background_supported is False

    restored = VisualProviderDescriptor.from_dict(by_alias["nano-banana"].to_dict())
    assert restored == by_alias["nano-banana"]


def test_visual_readiness_uses_nano_banana_default_and_surfaces_missing_credentials(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    readiness = get_visual_action_readiness(
        Path("workspace"),
        book_id="demo_book",
        visual_purpose="background_layer",
    )

    restored = VisualActionReadiness(**{k: v for k, v in readiness.to_dict().items() if k not in {"schema_version", "provider"}})
    assert restored.provider_id == "google"
    assert readiness.model_id == "gemini-2.5-flash-image"
    assert readiness.ready is False
    assert "GEMINI_API_KEY or GOOGLE_API_KEY" in readiness.missing_prerequisites
    assert "provider_adapter_missing" not in readiness.refusal_reasons


def test_visual_readiness_refuses_transparency_for_gpt_image_2() -> None:
    readiness = get_visual_action_readiness(
        Path("workspace"),
        book_id="demo_book",
        provider_model="gpt-image-2",
        visual_purpose="transparent_foreground_layer",
        transparent_background=True,
        require_credentials=False,
    )

    assert readiness.provider_id == "openai"
    assert readiness.allowed is False
    assert "unsupported_visual_purpose" in readiness.refusal_reasons
    assert "unsupported_transparent_background" in readiness.refusal_reasons
    assert "provider_adapter_missing" not in readiness.refusal_reasons


def test_visual_readiness_surfaces_missing_openai_credentials(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_KEY", raising=False)

    readiness = get_visual_action_readiness(
        Path("workspace"),
        book_id="demo_book",
        provider_model="gpt-image-2",
        visual_purpose="background_layer",
    )

    assert readiness.provider_id == "openai"
    assert readiness.ready is False
    assert "OPENAI_API_KEY or OPENAI_KEY" in readiness.missing_prerequisites
    assert "provider_adapter_missing" not in readiness.refusal_reasons


def test_visual_prompt_planning_readiness_does_not_require_provider_adapter_or_credentials(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    readiness = get_visual_action_readiness(
        Path("workspace"),
        book_id="demo_book",
        action="plan_visual_asset",
        require_credentials=True,
    )

    assert readiness.ready is True
    assert readiness.refusal_reasons == []
    assert readiness.missing_prerequisites == []


def test_visual_prompt_plan_action_writes_provisional_receipt(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "demo_book"
    book_root.mkdir(parents=True)

    request = build_plan_visual_asset_request(
        book_id="demo_book",
        prompt_text="A ruined glass city under a green aurora.",
        visual_purpose="background_layer",
    )
    result = plan_visual_asset_action(tmp_path, request)

    assert result.status == "success"
    assert result.details["provider_id"] == "google"
    assert result.details["model_id"] == "gemini-2.5-flash-image"
    assert result.produced_artifacts[0].artifact_status == "provisional"
    plan_path = Path(result.artifact_paths["visual_prompt_plan"])
    assert plan_path.exists()
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    assert payload["visual_purpose"] == "background_layer"
    assert "A ruined glass city" in payload["provider_prompt"]


def test_generate_visual_asset_uses_fake_provider_and_writes_artifacts(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "demo_book"
    book_root.mkdir(parents=True)
    plan_request = build_plan_visual_asset_request(
        book_id="demo_book",
        prompt_text="A clean isometric map of a moonlit archive.",
        visual_purpose="background_layer",
    )
    plan_result = plan_visual_asset_action(tmp_path, plan_request)

    def fake_generator(provider, prompt):
        assert provider.model_id == "gemini-2.5-flash-image"
        assert "moonlit archive" in prompt
        return GeneratedImage(
            bytes=b"fake-png-bytes",
            mime_type="image/png",
            provider_id=provider.provider_id,
            model_id=provider.model_id,
            text_parts=["created"],
            usage={"fake": True},
        )

    request = build_generate_visual_asset_request(
        book_id="demo_book",
        prompt_plan_path=plan_result.artifact_paths["visual_prompt_plan"],
        allow_spend=True,
    )
    result = generate_visual_asset_action(tmp_path, request, generator=fake_generator)

    assert result.status == "success"
    image_path = Path(result.artifact_paths["visual_image"])
    manifest_path = Path(result.artifact_paths["visual_asset_manifest"])
    assert image_path.exists()
    assert manifest_path.exists()
    assert image_path.read_bytes() == b"fake-png-bytes"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["provider_id"] == "google"
    assert manifest["model_id"] == "gemini-2.5-flash-image"
    assert manifest["artifact_status"] == "provisional"


def test_visual_asset_index_and_details_are_queryable(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "demo_book"
    book_root.mkdir(parents=True)
    plan_request = build_plan_visual_asset_request(
        book_id="demo_book",
        prompt_text="A clean isometric map of a moonlit archive.",
        visual_purpose="background_layer",
    )
    plan_result = plan_visual_asset_action(tmp_path, plan_request)

    request = build_generate_visual_asset_request(
        book_id="demo_book",
        prompt_plan_path=plan_result.artifact_paths["visual_prompt_plan"],
        allow_spend=True,
    )
    result = generate_visual_asset_action(
        tmp_path,
        request,
        generator=lambda provider, prompt: GeneratedImage(
            bytes=b"fake-png-bytes",
            mime_type="image/png",
            provider_id=provider.provider_id,
            model_id=provider.model_id,
        ),
    )

    index = get_visual_asset_index(tmp_path, "demo_book")
    assert index.prompt_plans[0].prompt_plan_id == plan_result.details["prompt_plan_id"]
    assert index.assets[0].asset_id == result.details["asset_id"]
    prompt_detail = get_visual_prompt_plan_detail(tmp_path, "demo_book", plan_result.details["prompt_plan_id"])
    assert "moonlit archive" in prompt_detail.payload["provider_prompt"]
    asset_detail = get_visual_asset_detail(tmp_path, "demo_book", result.details["asset_id"])
    assert asset_detail.asset.sha256 == result.details["sha256"]
    assert asset_detail.prompt_plan is not None
    assert asset_detail.prompt_plan.prompt_plan_id == plan_result.details["prompt_plan_id"]


def test_visual_actions_are_exposed_through_legal_next_actions(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "demo_book"
    book_root.mkdir(parents=True)
    selector = ScopeSelector(book_id="demo_book", workflow_family="visual_assets")

    options = {option.action: option for option in list_execution_options(tmp_path, selector)}

    assert options["plan_visual_asset"].allowed is True
    assert options["plan_visual_asset"].workflow_family == "visual_assets"
    assert options["generate_visual_asset"].allowed is False
    assert "prompt plan" in str(options["generate_visual_asset"].refusal_reason)

    plan_result = plan_visual_asset_action(
        tmp_path,
        build_plan_visual_asset_request(book_id="demo_book", prompt_text="A moonlit archive."),
    )
    options_after_plan = {option.action: option for option in list_execution_options(tmp_path, selector)}
    assert options_after_plan["generate_visual_asset"].allowed is True
    assert options_after_plan["generate_visual_asset"].details["prompt_plan_count"] == 1
    assert options_after_plan["generate_visual_asset"].details["available_prompt_plans"][0]["path"] == plan_result.artifact_paths["visual_prompt_plan"]


def test_openai_image_adapter_builds_request_and_extracts_base64(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    expected_bytes = b"fake-openai-png"
    seen = {}

    class FakeResponse:
        headers = {"Content-Type": "application/json"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(
                {
                    "data": [
                        {
                            "b64_json": base64.b64encode(expected_bytes).decode("ascii"),
                            "revised_prompt": "A revised moonlit archive prompt.",
                        }
                    ],
                    "usage": {"total_tokens": 7},
                }
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["headers"] = dict(request.header_items())
        seen["body"] = json.loads(request.data.decode("utf-8"))
        seen["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(visual_provider_module.urllib.request, "urlopen", fake_urlopen)
    provider = resolve_visual_provider("gpt-image-2")
    generated = generate_image_from_prompt(provider, "A moonlit archive.")

    assert generated.bytes == expected_bytes
    assert generated.provider_id == "openai"
    assert generated.model_id == "gpt-image-2"
    assert generated.mime_type == "image/png"
    assert generated.text_parts == ["A revised moonlit archive prompt."]
    assert generated.usage == {"total_tokens": 7}
    assert seen["url"] == "https://api.openai.com/v1/images/generations"
    assert seen["headers"]["Authorization"] == "Bearer test-openai-key"
    assert seen["body"]["model"] == "gpt-image-2"
    assert seen["body"]["prompt"] == "A moonlit archive."
    assert seen["body"]["size"] == "1024x1024"
    assert seen["timeout"] == 180


def test_generate_visual_asset_requires_explicit_spend_approval(tmp_path: Path) -> None:
    book_root = tmp_path / "books" / "demo_book"
    book_root.mkdir(parents=True)
    plan_request = build_plan_visual_asset_request(
        book_id="demo_book",
        prompt_text="A blue castle.",
    )
    plan_result = plan_visual_asset_action(tmp_path, plan_request)
    request = build_generate_visual_asset_request(
        book_id="demo_book",
        prompt_plan_path=plan_result.artifact_paths["visual_prompt_plan"],
    )

    try:
        generate_visual_asset_action(tmp_path, request, generator=lambda provider, prompt: None)
    except ValueError as exc:
        assert "allow_spend=true" in str(exc)
    else:
        raise AssertionError("Expected allow_spend guard to refuse generation.")


def test_visual_capabilities_are_projected() -> None:
    projection = get_capability_projection()
    by_id = {capability.capability_id: capability for capability in projection.capabilities}

    assert by_id["action.plan_visual_asset"].process_area == "visual_assets"
    assert by_id["action.generate_visual_asset"].approval_required is True
    assert by_id["action.plan_visual_asset"].details["default_provider_model"] == "nano-banana"
    assert "gpt-image-2" in by_id["action.plan_visual_asset"].details["option_provider_models"]
    assert by_id["query.visual_provider_descriptors"].mutation_class == "read_only"
    assert by_id["query.visual_asset_index"].process_area == "visual_assets"
    assert by_id["query.visual_asset_detail"].produced_artifact_statuses == ["provisional", "diagnostic"]
    assert by_id["readiness.visual_action_readiness"].capability_type == "readiness"
    assert by_id["gap.visual.reference_image_workflows"].implementation_status == "designed_gap"


def test_cli_parses_visual_commands() -> None:
    parser = build_parser()

    providers = parser.parse_args(["visual", "providers", "--json"])
    readiness = parser.parse_args(["visual", "readiness", "--book", "demo_book", "--model", "gpt-image-2"])
    plan = parser.parse_args(["visual", "plan", "--book", "demo_book", "--prompt-text", "A moonlit archive."])
    generate = parser.parse_args(["visual", "generate", "--book", "demo_book", "--prompt-plan", "plan.json", "--allow-spend"])
    artifacts = parser.parse_args(["visual", "artifacts", "--book", "demo_book", "--json"])
    asset = parser.parse_args(["visual", "asset", "--book", "demo_book", "--asset-id", "visual_asset_1"])
    prompt_plan = parser.parse_args(["visual", "prompt-plan", "--book", "demo_book", "--prompt-plan", "visual_prompt_plan_1"])
    visual_legal = parser.parse_args(["workflow", "legal-actions", "--book", "demo_book", "--workflow-family", "visual_assets", "--json"])

    assert providers.command == "visual"
    assert providers.visual_command == "providers"
    assert readiness.model == "gpt-image-2"
    assert plan.prompt_text == "A moonlit archive."
    assert generate.allow_spend is True
    assert artifacts.visual_command == "artifacts"
    assert asset.asset_id == "visual_asset_1"
    assert prompt_plan.prompt_plan == "visual_prompt_plan_1"
    assert visual_legal.workflow_family == "visual_assets"
    assert visual_legal.json is True
