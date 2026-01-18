from __future__ import annotations

from typing import Iterable

from .client import LLMClient
from .types import LLMResponse, Message
from .utils import post_json


class OllamaClient(LLMClient):
    def __init__(self, api_url: str) -> None:
        super().__init__(provider="ollama")
        self.api_url = api_url.rstrip("/") + "/api/chat"

    def chat(
        self,
        messages: Iterable[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        payload = {
            "model": model,
            "messages": list(messages),
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        headers = {"Content-Type": "application/json"}
        raw = post_json(self.api_url, payload, headers)
        message = raw.get("message", {})
        text = message.get("content", "")
        prompt_tokens = raw.get("prompt_eval_count")
        completion_tokens = raw.get("eval_count")
        total_tokens = None
        if prompt_tokens is not None and completion_tokens is not None:
            total_tokens = prompt_tokens + completion_tokens
        return LLMResponse(
            text=text,
            raw=raw,
            provider=self.provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
