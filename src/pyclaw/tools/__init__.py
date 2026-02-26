"""PyClaw custom tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyclaw.tools.web_search import build_web_search_tool

if TYPE_CHECKING:
    from pyclaw.config import PyClawConfig


def build_tools(config: PyClawConfig) -> list:
    """Build the list of custom tools based on config."""
    tools = []

    # Web search
    web_cfg = config.tools.web_search
    if web_cfg.enabled:
        tools.append(build_web_search_tool(web_cfg))

    # Cron/heartbeat management
    from pyclaw.tools.cron_tool import build_cron_tools

    tools.extend(build_cron_tools(config.workspace_path))

    # Cross-channel messaging (only if any channel is enabled)
    channels_cfg = config.channels
    if (
        channels_cfg.telegram.enabled
        or channels_cfg.discord.enabled
        or channels_cfg.slack.enabled
    ):
        from pyclaw.tools.message import build_message_tool

        tools.append(build_message_tool(config))

    return tools
