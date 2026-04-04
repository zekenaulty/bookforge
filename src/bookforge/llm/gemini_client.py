from __future__ import annotations

from typing import Iterable, Optional

from .client import LLMClient
from .rate_limiter import RateLimiter
from .types import LLMResponse, Message
from .utils import post_json, split_system_messages


class GeminiClient(LLMClient):
    def __init__(self, api_key: str, api_url: str, rate_limiter: Optional[RateLimiter] = None, timeout_seconds: int = 240, key_slot: Optional[str] = None) -> None:
        super().__init__(provider="gemini", rate_limiter=rate_limiter, key_slot=key_slot)
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def chat(
        self,
        messages: Iterable[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        thinking_level: Optional[str] = None,
    ) -> LLMResponse:
        self._throttle()
        system_text, non_system = split_system_messages(messages)
        contents = []
        for msg in non_system:
            role = msg.get("role", "user")
            gemini_role = "model" if role == "assistant" else "user"
            parts = msg.get("parts")
            if isinstance(parts, list) and parts:
                contents.append({"role": gemini_role, "parts": parts})
            else:
                contents.append({"role": gemini_role, "parts": [{"text": msg.get("content", "")} ]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        normalized_level = str(thinking_level or "").strip().lower()
        if normalized_level in {"minimal", "low", "medium", "high"}:
            payload["generationConfig"]["thinkingConfig"] = {
                "thinkingLevel": normalized_level
            }
        if system_text:
            payload["system_instruction"] = {"parts": [{"text": system_text}]}

        url = f"{self.api_url}/models/{model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        raw = post_json(url, payload, headers, timeout=self.timeout_seconds, max_retries=3)
        candidates = raw.get("candidates", [])
        text = ""
        assistant_parts = []
        if candidates:
            assistant_parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join([part.get("text", "") for part in assistant_parts if isinstance(part, dict)])
        return LLMResponse(
            text=text,
            raw=raw,
            provider=self.provider,
            model=model,
            assistant_parts=assistant_parts if isinstance(assistant_parts, list) else None,
        )
