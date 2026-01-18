from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional
from .types import LLMResponse, Message
from .rate_limiter import RateLimiter


class LLMClient(ABC):
    def __init__(self, provider: str, rate_limiter: Optional[RateLimiter] = None) -> None:
        self.provider = provider
        self.rate_limiter = rate_limiter

    def _throttle(self) -> None:
        if self.rate_limiter:
            self.rate_limiter.wait()

    @abstractmethod
    def chat(
        self,
        messages: Iterable[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        raise NotImplementedError
