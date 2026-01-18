from __future__ import annotations

from typing import Iterable

from .client import LLMClient
from .types import LLMResponse, Message
from .utils import post_json, split_system_messages


class GeminiClient(LLMClient):
    def __init__(self, api_key: str, api_url: str) -> None:
        super().__init__(provider="gemini")
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")

    def chat(
        self,
        messages: Iterable[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        system_text, non_system = split_system_messages(messages)
        contents = []
        for msg in non_system:
            role = msg.get("role", "user")
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({"role": gemini_role, "parts": [{"text": msg.get("content", "")} ]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_text:
            payload["system_instruction"] = {"parts": [{"text": system_text}]}

        url = f"{self.api_url}/models/{model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        raw = post_json(url, payload, headers)
        candidates = raw.get("candidates", [])
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join([part.get("text", "") for part in parts])
        return LLMResponse(
            text=text,
            raw=raw,
            provider=self.provider,
            model=model,
        )
