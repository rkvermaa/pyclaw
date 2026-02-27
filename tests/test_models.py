"""Tests for the YAML-driven model registry."""

from __future__ import annotations

from pyclaw.models import load_model_registry


def test_load_registry():
    """Registry should load all providers from models.yml."""
    load_model_registry.cache_clear()
    registry = load_model_registry()
    keys = [p.key for p in registry.providers]
    assert "openai" in keys
    assert "anthropic" in keys
    assert "google_genai" in keys
    assert "deepseek" in keys
    assert "ollama" in keys


def test_get_provider():
    """get_provider should return the correct ProviderDef."""
    load_model_registry.cache_clear()
    registry = load_model_registry()
    ds = registry.get_provider("deepseek")
    assert ds is not None
    assert ds.langchain_provider == "openai"
    assert ds.base_url == "https://api.deepseek.com"
    assert ds.needs_api_key is True


def test_get_provider_not_found():
    """get_provider should return None for unknown keys."""
    load_model_registry.cache_clear()
    registry = load_model_registry()
    assert registry.get_provider("nonexistent") is None


def test_get_provider_for_model_string_deepseek():
    """Parsing 'deepseek:deepseek-chat' should resolve correctly."""
    load_model_registry.cache_clear()
    registry = load_model_registry()
    provider, model_id = registry.get_provider_for_model_string("deepseek:deepseek-chat")
    assert provider is not None
    assert provider.key == "deepseek"
    assert model_id == "deepseek-chat"


def test_get_provider_for_model_string_no_colon():
    """A plain model string with no colon should return (None, original)."""
    load_model_registry.cache_clear()
    registry = load_model_registry()
    provider, model_id = registry.get_provider_for_model_string("gpt-4o")
    assert provider is None
    assert model_id == "gpt-4o"


def test_deepseek_models():
    """DeepSeek should have multiple models listed."""
    load_model_registry.cache_clear()
    registry = load_model_registry()
    ds = registry.get_provider("deepseek")
    assert ds is not None
    model_ids = [m.id for m in ds.models]
    assert "deepseek-chat" in model_ids
    assert "deepseek-reasoner" in model_ids


def test_ollama_no_api_key():
    """Ollama should not require an API key."""
    load_model_registry.cache_clear()
    registry = load_model_registry()
    ollama = registry.get_provider("ollama")
    assert ollama is not None
    assert ollama.needs_api_key is False
