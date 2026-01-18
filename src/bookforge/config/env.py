from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import os


@dataclass(frozen=True)
class AppConfig:
    provider: str
    openai_api_key: Optional[str]
    gemini_api_key: Optional[str]
    ollama_url: str
    openai_api_url: str
    gemini_api_url: str
    planner_model: Optional[str]
    writer_model: Optional[str]
    linter_model: Optional[str]
    default_model: Optional[str]
    gemini_requests_per_minute: Optional[int]
    task_model_overrides: Dict[str, str]
    task_provider_overrides: Dict[str, str]


def _parse_env_file(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    data: Dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def _extract_prefixed(env: Dict[str, str], prefix: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for key, value in env.items():
        if not key.startswith(prefix):
            continue
        suffix = key[len(prefix):].strip().lower()
        if not suffix:
            continue
        values[suffix] = value
    return values


def load_config(env: Optional[Dict[str, str]] = None, env_path: Optional[str] = ".env") -> AppConfig:
    merged: Dict[str, str] = {}
    if env_path:
        merged.update(_parse_env_file(Path(env_path)))
    merged.update(env or os.environ)

    provider = (merged.get("LLM_PROVIDER") or "openai").lower()
    openai_url = merged.get("OPENAI_API_URL") or "https://api.openai.com/v1/chat/completions"
    gemini_url = merged.get("GEMINI_API_URL") or "https://generativelanguage.googleapis.com/v1beta"
    ollama_url = merged.get("OLLAMA_URL") or "http://localhost:11434"

    task_model_overrides = _extract_prefixed(merged, "TASK_MODEL_")
    task_provider_overrides = _extract_prefixed(merged, "TASK_PROVIDER_")

    gemini_rpm = merged.get("GEMINI_REQUESTS_PER_MINUTE")
    try:
        gemini_rpm_val = int(gemini_rpm) if gemini_rpm is not None and str(gemini_rpm).strip() else None
    except ValueError:
        gemini_rpm_val = None

    return AppConfig(
        provider=provider,
        openai_api_key=merged.get("OPENAI_API_KEY"),
        gemini_api_key=merged.get("GEMINI_API_KEY"),
        ollama_url=ollama_url,
        openai_api_url=openai_url,
        gemini_api_url=gemini_url,
        planner_model=merged.get("PLANNER_MODEL"),
        writer_model=merged.get("WRITER_MODEL"),
        linter_model=merged.get("LINTER_MODEL"),
        default_model=merged.get("DEFAULT_MODEL"),
        gemini_requests_per_minute=gemini_rpm_val,
        task_model_overrides=task_model_overrides,
        task_provider_overrides=task_provider_overrides,
    )


def validate_provider_config(config: AppConfig) -> None:
    if config.provider == "openai":
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return
    if config.provider == "gemini":
        if not config.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        return
    if config.provider == "ollama":
        if not config.ollama_url:
            raise ValueError("OLLAMA_URL is required when LLM_PROVIDER=ollama")
        return
    raise ValueError(f"Unsupported LLM_PROVIDER: {config.provider}")
