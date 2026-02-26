"""PyClaw configuration system using Pydantic."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

DEFAULT_CONFIG_DIR = Path.home() / ".pyclaw"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.json"
DEFAULT_ENV_PATH = DEFAULT_CONFIG_DIR / ".env"
DEFAULT_WORKSPACE = DEFAULT_CONFIG_DIR / "workspace"


class ModelEntry(BaseModel):
    name: str
    provider: str
    model: str
    api_key_env: str = ""
    base_url: str = ""


class WebSearchConfig(BaseModel):
    enabled: bool = True
    provider: str = "tavily"
    api_key_env: str = "TAVILY_API_KEY"


class ShellExecConfig(BaseModel):
    enabled: bool = True


class ToolsConfig(BaseModel):
    web_search: WebSearchConfig = Field(default_factory=WebSearchConfig)
    shell_exec: ShellExecConfig = Field(default_factory=ShellExecConfig)


class ChannelConfig(BaseModel):
    enabled: bool = False
    token_env: str = ""


class TelegramConfig(ChannelConfig):
    token_env: str = "TELEGRAM_BOT_TOKEN"
    allowed_users: list[int] = Field(default_factory=list)


class DiscordConfig(ChannelConfig):
    token_env: str = "DISCORD_BOT_TOKEN"


class SlackConfig(ChannelConfig):
    token_env: str = "SLACK_BOT_TOKEN"


class ChannelsConfig(BaseModel):
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    slack: SlackConfig = Field(default_factory=SlackConfig)


class HeartbeatConfig(BaseModel):
    enabled: bool = False
    interval_minutes: int = 60


class PyClawConfig(BaseModel):
    default_model: str = "openai:gpt-4o"
    model_list: list[ModelEntry] = Field(default_factory=lambda: [
        ModelEntry(
            name="gpt-4o",
            provider="openai",
            model="gpt-4o",
            api_key_env="OPENAI_API_KEY",
        ),
        ModelEntry(
            name="claude",
            provider="anthropic",
            model="claude-sonnet-4-5-20250929",
            api_key_env="ANTHROPIC_API_KEY",
        ),
        ModelEntry(
            name="local-llama",
            provider="ollama",
            model="llama3.2",
            base_url="http://localhost:11434",
        ),
    ])
    workspace: str = str(DEFAULT_WORKSPACE)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    heartbeat: HeartbeatConfig = Field(default_factory=HeartbeatConfig)

    @property
    def workspace_path(self) -> Path:
        return Path(self.workspace).expanduser()


def load_config(path: Path | None = None) -> PyClawConfig:
    """Load config from JSON file, or return defaults if file doesn't exist."""
    config_path = path or DEFAULT_CONFIG_PATH
    if config_path.exists():
        data = json.loads(config_path.read_text(encoding="utf-8"))
        return PyClawConfig.model_validate(data)
    return PyClawConfig()


def save_config(config: PyClawConfig, path: Path | None = None) -> Path:
    """Save config to JSON file."""
    config_path = path or DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        config.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return config_path
