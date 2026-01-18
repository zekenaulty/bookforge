from __future__ import annotations

from typing import Iterable, Optional

from .client import LLMClient
from .rate_limiter import RateLimiter
from .types import LLMResponse, Message
from .utils import post_json


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, api_url: str, rate_limiter: Optional[RateLimiter] = None) -> None:
        super().__init__(provider="openai", rate_limiter=rate_limiter)
        self.api_key = api_key
        self.api_url = api_url

    def chat(
        self,
        messages: Iterable[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        self._throttle()
        payload = {
            "model": model,
            "messages": list(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        raw = post_json(self.api_url, payload, headers, max_retries=3)
        choice = raw.get("choices", [{}])[0]
        message = choice.get("message", {})
        text = message.get("content", "")
        usage = raw.get("usage") or {}
        return LLMResponse(
            text=text,
            raw=raw,
            provider=self.provider,
            model=model,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
        )
