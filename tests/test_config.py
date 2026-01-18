import pytest

from bookforge.config.env import load_config, validate_provider_config


def test_default_provider_is_openai():
    config = load_config(env={}, env_path=None)
    assert config.provider == "openai"


def test_openai_requires_key():
    config = load_config(env={"LLM_PROVIDER": "openai"}, env_path=None)
    with pytest.raises(ValueError):
        validate_provider_config(config)


def test_gemini_requires_key():
    config = load_config(env={"LLM_PROVIDER": "gemini"}, env_path=None)
    with pytest.raises(ValueError):
        validate_provider_config(config)


def test_ollama_does_not_require_key():
    config = load_config(env={"LLM_PROVIDER": "ollama"}, env_path=None)
    validate_provider_config(config)
