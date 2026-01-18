import pytest

from bookforge.config.env import load_config
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.openai_client import OpenAIClient
from bookforge.llm.gemini_client import GeminiClient
from bookforge.llm.ollama_client import OllamaClient


def test_factory_openai_client():
    config = load_config(
        env={"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "x"},
        env_path=None,
    )
    client = get_llm_client(config)
    assert isinstance(client, OpenAIClient)


def test_factory_gemini_client():
    config = load_config(
        env={"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "x"},
        env_path=None,
    )
    client = get_llm_client(config)
    assert isinstance(client, GeminiClient)


def test_factory_ollama_client():
    config = load_config(env={"LLM_PROVIDER": "ollama"}, env_path=None)
    client = get_llm_client(config)
    assert isinstance(client, OllamaClient)


def test_factory_unknown_provider():
    config = load_config(env={"LLM_PROVIDER": "unknown"}, env_path=None)
    with pytest.raises(ValueError):
        get_llm_client(config)


def test_resolve_model_phase_specific_over_default():
    config = load_config(
        env={
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "x",
            "DEFAULT_MODEL": "base",
            "PLANNER_MODEL": "planner",
        },
        env_path=None,
    )
    assert resolve_model("planner", config) == "planner"


def test_resolve_model_falls_back_to_default():
    config = load_config(
        env={
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "x",
            "DEFAULT_MODEL": "base",
        },
        env_path=None,
    )
    assert resolve_model("writer", config) == "base"
