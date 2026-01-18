from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable
from .types import LLMResponse, Message


class LLMClient(ABC):
    def __init__(self, provider: str) -> None:
        self.provider = provider

    @abstractmethod
    def chat(
        self,
        messages: Iterable[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        raise NotImplementedError
