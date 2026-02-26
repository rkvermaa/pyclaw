"""PyClaw channel gateways."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyclaw.channels.base import BaseChannel
    from pyclaw.config import PyClawConfig


def get_enabled_channels(config: PyClawConfig) -> dict[str, BaseChannel]:
    """Return instantiated channel objects for all enabled channels."""
    channels: dict[str, BaseChannel] = {}

    if config.channels.telegram.enabled:
        from pyclaw.channels.telegram import TelegramChannel

        channels["telegram"] = TelegramChannel(config)

    if config.channels.discord.enabled:
        from pyclaw.channels.discord_ch import DiscordChannel

        channels["discord"] = DiscordChannel(config)

    if config.channels.slack.enabled:
        from pyclaw.channels.slack_ch import SlackChannel

        channels["slack"] = SlackChannel(config)

    return channels
