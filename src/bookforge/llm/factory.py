from __future__ import annotations

from typing import Optional

from bookforge.config.env import AppConfig, validate_provider_config
from .client import LLMClient
from .openai_client import OpenAIClient
from .gemini_client import GeminiClient
from .ollama_client import OllamaClient


def get_llm_client(config: AppConfig) -> LLMClient:
    validate_provider_config(config)
    if config.provider == "openai":
        return OpenAIClient(config.openai_api_key or "", config.openai_api_url)
    if config.provider == "gemini":
        return GeminiClient(config.gemini_api_key or "", config.gemini_api_url)
    if config.provider == "ollama":
        return OllamaClient(config.ollama_url)
    raise ValueError(f"Unsupported LLM_PROVIDER: {config.provider}")


def resolve_model(phase: str, config: AppConfig) -> str:
    phase_key = phase.lower()
    model: Optional[str] = None
    if phase_key == "planner":
        model = config.planner_model
    elif phase_key == "writer":
        model = config.writer_model
    elif phase_key == "linter":
        model = config.linter_model

    if model:
        return model
    if config.default_model:
        return config.default_model
    raise ValueError(f"Model not configured for phase: {phase}")
