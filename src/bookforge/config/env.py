from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import os

from bookforge.util.paths import repo_root

@dataclass(frozen=True)
class AppConfig:
    provider: str
    openai_api_key: Optional[str]
    gemini_api_key: Optional[str]
    planner_api_key: Optional[str]
    writer_api_key: Optional[str]
    repair_api_key: Optional[str]
    linter_api_key: Optional[str]
    continuity_api_key: Optional[str]
    ollama_url: str
    openai_api_url: str
    gemini_api_url: str
    request_timeout_seconds: int
    planner_model: Optional[str]
    writer_model: Optional[str]
    repair_model: Optional[str]
    linter_model: Optional[str]
    continuity_model: Optional[str]
    default_model: Optional[str]
    gemini_requests_per_minute: Optional[int]
    task_model_overrides: Dict[str, str]
    task_provider_overrides: Dict[str, str]


def _parse_env_file(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    data: Dict[str, str] = {}
    # Use utf-8-sig to drop a BOM that would otherwise prefix the first key.
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
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



def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None

def _default_env_path() -> Path:
    return repo_root(Path(__file__).resolve()) / ".env"


def load_config(env: Optional[Dict[str, str]] = None, env_path: Optional[str] = None) -> AppConfig:
    merged: Dict[str, str] = {}
    env_file: Optional[Path] = None
    if env_path is None:
        if env is None:
            env_file = _default_env_path()
    elif env_path:
        env_file = Path(env_path)
    merged.update(os.environ)
    if env_file:
        merged.update(_parse_env_file(env_file))
    if env is not None:
        merged.update(env)

    provider = (merged.get("LLM_PROVIDER") or "openai").lower()
    openai_url = merged.get("OPENAI_API_URL") or "https://api.openai.com/v1/chat/completions"
    gemini_url = merged.get("GEMINI_API_URL") or "https://generativelanguage.googleapis.com/v1beta"
    ollama_url = merged.get("OLLAMA_URL") or "http://localhost:11434"

    task_model_overrides = _extract_prefixed(merged, "TASK_MODEL_")
    task_provider_overrides = _extract_prefixed(merged, "TASK_PROVIDER_")

    gemini_rpm_val = _parse_int(merged.get("GEMINI_REQUESTS_PER_MINUTE"))
    timeout_val = _parse_int(merged.get("BOOKFORGE_REQUEST_TIMEOUT_SECONDS"))
    if timeout_val is None:
        timeout_val = 600

    return AppConfig(
        provider=provider,
        openai_api_key=merged.get("OPENAI_API_KEY"),
        gemini_api_key=merged.get("GEMINI_API_KEY"),
        planner_api_key=merged.get("PLANNER_API_KEY"),
        writer_api_key=merged.get("WRITER_API_KEY"),
        repair_api_key=merged.get("REPAIR_API_KEY"),
        linter_api_key=merged.get("LINTER_API_KEY"),
        continuity_api_key=merged.get("CONTINUITY_API_KEY"),
        ollama_url=ollama_url,
        openai_api_url=openai_url,
        gemini_api_url=gemini_url,
        request_timeout_seconds=timeout_val,
        planner_model=merged.get("PLANNER_MODEL"),
        writer_model=merged.get("WRITER_MODEL"),
        repair_model=merged.get("REPAIR_MODEL"),
        linter_model=merged.get("LINTER_MODEL"),
        continuity_model=merged.get("CONTINUITY_MODEL"),
        default_model=merged.get("DEFAULT_MODEL"),
        gemini_requests_per_minute=gemini_rpm_val,
        task_model_overrides=task_model_overrides,
        task_provider_overrides=task_provider_overrides,
    )



def read_env_value(name: str) -> Optional[str]:
    env_path = _default_env_path()
    data = _parse_env_file(env_path)
    if name in data:
        return data.get(name)
    return os.environ.get(name)


def read_int_env(name: str, default: int) -> int:
    raw = read_env_value(name)
    if raw is None:
        return default
    raw = str(raw).strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default




def _has_phase_api_keys(config: AppConfig) -> bool:
    return any([
        config.planner_api_key,
        config.writer_api_key,
        config.repair_api_key,
        config.linter_api_key,
        config.continuity_api_key,
    ])


def validate_provider_config(config: AppConfig) -> None:
    if config.provider == "openai":
        if not (config.openai_api_key or _has_phase_api_keys(config)):
            raise ValueError("OPENAI_API_KEY or phase API key is required when LLM_PROVIDER=openai")
        return
    if config.provider == "gemini":
        if not (config.gemini_api_key or _has_phase_api_keys(config)):
            raise ValueError("GEMINI_API_KEY or phase API key is required when LLM_PROVIDER=gemini")
        return
    if config.provider == "ollama":
        if not config.ollama_url:
            raise ValueError("OLLAMA_URL is required when LLM_PROVIDER=ollama")
        return
    raise ValueError(f"Unsupported LLM_PROVIDER: {config.provider}")
