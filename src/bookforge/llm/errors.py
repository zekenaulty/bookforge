from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass(frozen=True)
class QuotaViolation:
    quota_metric: str
    quota_id: str
    quota_dimensions: Dict[str, str]
    quota_value: str

@dataclass(frozen=True)
class LLMRequestError(Exception):
    status_code: int
    message: str
    retry_after_seconds: Optional[float]
    quota_violations: List[QuotaViolation]
    raw_response: Any

    def __str__(self) -> str:
        base = f"HTTP {self.status_code}: {self.message}"
        if self.retry_after_seconds is not None:
            base += f" (retry after {self.retry_after_seconds:.2f}s)"
        return base
