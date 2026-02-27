"""Tests for PyClaw configuration system."""

from __future__ import annotations

from pathlib import Path

from pyclaw.config import PyClawConfig, load_config, save_config


def test_default_config():
    """Default config should have sensible defaults."""
    config = PyClawConfig()
    assert config.default_model == "openai:gpt-4o"
    assert len(config.model_list) == 4
    # DeepSeek provider should be 'deepseek' (not 'openai')
    ds = next(m for m in config.model_list if m.name == "deepseek")
    assert ds.provider == "deepseek"
    assert config.tools.web_search.enabled is True
    assert config.tools.shell_exec.enabled is True
    assert config.heartbeat.enabled is False
    assert config.channels.telegram.enabled is False


def test_save_and_load_config(config_path: Path):
    """Config should round-trip through save/load."""
    config = PyClawConfig(default_model="anthropic:claude-sonnet-4-5-20250929")
    save_config(config, config_path)

    loaded = load_config(config_path)
    assert loaded.default_model == "anthropic:claude-sonnet-4-5-20250929"
    assert loaded.tools.web_search.enabled is True


def test_load_missing_config(tmp_path: Path):
    """Loading from non-existent path should return defaults."""
    config = load_config(tmp_path / "nonexistent.json")
    assert config.default_model == "openai:gpt-4o"


def test_workspace_path():
    """workspace_path property should expand ~ correctly."""
    config = PyClawConfig(workspace="~/test_workspace")
    assert config.workspace_path == Path.home() / "test_workspace"


def test_config_with_custom_tools():
    """Config should accept custom tool settings."""
    config = PyClawConfig.model_validate({
        "default_model": "openai:gpt-4o",
        "tools": {
            "web_search": {"enabled": False, "provider": "duckduckgo"},
            "shell_exec": {"enabled": False},
        },
    })
    assert config.tools.web_search.enabled is False
    assert config.tools.web_search.provider == "duckduckgo"
    assert config.tools.shell_exec.enabled is False


def test_config_with_channels():
    """Config should accept channel settings."""
    config = PyClawConfig.model_validate({
        "default_model": "openai:gpt-4o",
        "channels": {
            "telegram": {"enabled": True, "allowed_users": [12345]},
            "discord": {"enabled": True},
        },
    })
    assert config.channels.telegram.enabled is True
    assert config.channels.telegram.allowed_users == [12345]
    assert config.channels.discord.enabled is True
    assert config.channels.slack.enabled is False
