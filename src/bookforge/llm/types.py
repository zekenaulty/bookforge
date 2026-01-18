from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

Message = Dict[str, str]


@dataclass
class LLMResponse:
    text: str
    raw: Any
    provider: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
