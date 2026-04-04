from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, List

Message = Dict[str, Any]


@dataclass
class LLMResponse:
    text: str
    raw: Any
    provider: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    assistant_parts: Optional[List[Dict[str, Any]]] = None
