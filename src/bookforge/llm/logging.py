from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import json
import os

from .types import LLMResponse


def should_log_llm() -> bool:
    flag = os.environ.get("BOOKFORGE_LOG_LLM", "").strip().lower()
    return flag in {"1", "true", "yes", "on"}


def llm_log_dir(workspace: Path) -> Path:
    return workspace / "logs" / "llm"


def log_llm_response(
    workspace: Path,
    label: str,
    response: LLMResponse,
    extra: Optional[Dict[str, Any]] = None,
) -> Path:
    log_dir = llm_log_dir(workspace)
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"{label}_{timestamp}.json"
    payload: Dict[str, Any] = {
        "label": label,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "provider": response.provider,
        "model": response.model,
        "text": response.text,
        "raw": response.raw,
    }
    if extra:
        payload["extra"] = extra
    log_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return log_path
