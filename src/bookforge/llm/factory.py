from __future__ import annotations

from typing import Optional

from bookforge.config.env import AppConfig, validate_provider_config
from .client import LLMClient
from .rate_limiter import RateLimiter

from .openai_client import OpenAIClient
from .gemini_client import GeminiClient
from .ollama_client import OllamaClient

_RATE_LIMITERS: dict[tuple[str, str], RateLimiter] = {}


def _select_api_key(config: AppConfig, phase: Optional[str], default_key: Optional[str]) -> tuple[Optional[str], str]:
    phase_key = (phase or "").lower()
    override = None
    if phase_key == "planner":
        override = config.planner_api_key
    elif phase_key == "preflight":
        override = config.preflight_api_key
    elif phase_key == "writer":
        override = config.writer_api_key
    elif phase_key == "repair":
        override = config.repair_api_key
    elif phase_key == "state_repair":
        override = config.state_repair_api_key
    elif phase_key == "linter":
        override = config.linter_api_key
    elif phase_key == "continuity":
        override = config.continuity_api_key
    elif phase_key == "characters":
        override = config.characters_api_key
    if override:
        return override, phase_key
    return default_key, "default"


def _shared_rate_limiter(provider: str, key_slot: str, rpm: int | None) -> RateLimiter | None:
    if not rpm or rpm <= 0:
        return None
    slot = key_slot or "default"
    key = (provider, slot)
    limiter = _RATE_LIMITERS.get(key)
    if limiter is None:
        limiter = RateLimiter(rpm)
        _RATE_LIMITERS[key] = limiter
    return limiter


def get_llm_client(config: AppConfig, phase: Optional[str] = None) -> LLMClient:
    validate_provider_config(config)
    rate_limiter = None
    if config.provider == "openai":
        api_key, key_slot = _select_api_key(config, phase, config.openai_api_key)
        if not api_key:
            raise ValueError("OPENAI_API_KEY or phase API key is required for this phase")
        return OpenAIClient(api_key, config.openai_api_url, rate_limiter=rate_limiter, timeout_seconds=config.request_timeout_seconds, key_slot=key_slot)
    if config.provider == "gemini":
        api_key, key_slot = _select_api_key(config, phase, config.gemini_api_key)
        if not api_key:
            raise ValueError("GEMINI_API_KEY or phase API key is required for this phase")
        rate_limiter = _shared_rate_limiter("gemini", key_slot, config.gemini_requests_per_minute)
        return GeminiClient(api_key, config.gemini_api_url, rate_limiter=rate_limiter, timeout_seconds=config.request_timeout_seconds, key_slot=key_slot)
    if config.provider == "ollama":
        return OllamaClient(config.ollama_url, rate_limiter=rate_limiter, timeout_seconds=config.request_timeout_seconds, key_slot="ollama")
    raise ValueError(f"Unsupported LLM_PROVIDER: {config.provider}")


def resolve_model(phase: str, config: AppConfig) -> str:
    phase_key = phase.lower()
    model: Optional[str] = None
    if phase_key == "planner":
        model = config.planner_model
    elif phase_key == "preflight":
        model = config.preflight_model
    elif phase_key == "writer":
        model = config.writer_model
    elif phase_key == "repair":
        model = config.repair_model
    elif phase_key == "state_repair":
        model = config.state_repair_model
    elif phase_key == "linter":
        model = config.linter_model
    elif phase_key == "continuity":
        model = config.continuity_model
    elif phase_key == "characters":
        model = config.characters_model

    if model:
        return model
    if config.default_model:
        return config.default_model
    raise ValueError(f"Model not configured for phase: {phase}")
