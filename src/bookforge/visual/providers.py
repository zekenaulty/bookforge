from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from bookforge.contracts import VisualProviderDescriptor


@dataclass(frozen=True, slots=True)
class GeneratedImage:
    bytes: bytes
    mime_type: str
    provider_id: str
    model_id: str
    text_parts: List[str] = field(default_factory=list)
    usage: Dict[str, Any] = field(default_factory=dict)
    raw_response: Dict[str, Any] = field(default_factory=dict)


def _google_api_key() -> str:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY is required for Nano Banana image generation.")
    return api_key


def _openai_api_key() -> str:
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY or OPENAI_KEY is required for GPT Image generation.")
    return api_key


def _extract_google_image(payload: Dict[str, Any]) -> tuple[bytes, str, List[str]]:
    text_parts: List[str] = []
    candidates = payload.get("candidates") if isinstance(payload.get("candidates"), list) else []
    for candidate in candidates:
        content = candidate.get("content") if isinstance(candidate, dict) else None
        parts = content.get("parts") if isinstance(content, dict) and isinstance(content.get("parts"), list) else []
        for part in parts:
            if not isinstance(part, dict):
                continue
            if isinstance(part.get("text"), str) and part["text"].strip():
                text_parts.append(part["text"].strip())
            inline = part.get("inlineData") or part.get("inline_data")
            if isinstance(inline, dict) and inline.get("data"):
                mime_type = str(inline.get("mimeType") or inline.get("mime_type") or "image/png")
                return base64.b64decode(str(inline["data"])), mime_type, text_parts
    raise RuntimeError("Gemini image response did not include inline image data.")


def _generate_google_image(provider: VisualProviderDescriptor, prompt: str) -> GeneratedImage:
    api_key = _google_api_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{provider.model_id}:generateContent"
    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ]
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini image generation failed: HTTP {exc.code}: {detail}") from exc
    image_bytes, mime_type, text_parts = _extract_google_image(payload)
    usage = payload.get("usageMetadata") if isinstance(payload.get("usageMetadata"), dict) else {}
    return GeneratedImage(
        bytes=image_bytes,
        mime_type=mime_type,
        provider_id=provider.provider_id,
        model_id=provider.model_id,
        text_parts=text_parts,
        usage=usage,
        raw_response=payload,
    )


def _extract_openai_image(payload: Dict[str, Any]) -> tuple[bytes, str, List[str]]:
    data = payload.get("data") if isinstance(payload.get("data"), list) else []
    if not data:
        raise RuntimeError("OpenAI image response did not include data.")
    first = data[0] if isinstance(data[0], dict) else {}
    text_parts: List[str] = []
    revised_prompt = first.get("revised_prompt")
    if isinstance(revised_prompt, str) and revised_prompt.strip():
        text_parts.append(revised_prompt.strip())
    b64_data = first.get("b64_json")
    if isinstance(b64_data, str) and b64_data:
        return base64.b64decode(b64_data), "image/png", text_parts
    image_url = first.get("url")
    if isinstance(image_url, str) and image_url:
        with urllib.request.urlopen(image_url, timeout=180) as response:
            content_type = response.headers.get("Content-Type") or "image/png"
            return response.read(), content_type, text_parts
    raise RuntimeError("OpenAI image response did not include b64_json or url image data.")


def _generate_openai_image(provider: VisualProviderDescriptor, prompt: str) -> GeneratedImage:
    api_key = _openai_api_key()
    body = {
        "model": provider.model_id,
        "prompt": prompt,
        "size": "1024x1024",
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI image generation failed: HTTP {exc.code}: {detail}") from exc
    image_bytes, mime_type, text_parts = _extract_openai_image(payload)
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    return GeneratedImage(
        bytes=image_bytes,
        mime_type=mime_type,
        provider_id=provider.provider_id,
        model_id=provider.model_id,
        text_parts=text_parts,
        usage=usage,
        raw_response=payload,
    )


def generate_image_from_prompt(provider: VisualProviderDescriptor, prompt: str) -> GeneratedImage:
    if provider.provider_id == "google" and provider.model_id == "gemini-2.5-flash-image":
        return _generate_google_image(provider, prompt)
    if provider.provider_id == "openai" and provider.model_id == "gpt-image-2":
        return _generate_openai_image(provider, prompt)
    raise RuntimeError(f"No visual provider adapter is available for {provider.key}.")
