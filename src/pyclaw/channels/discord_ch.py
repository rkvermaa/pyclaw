"""Discord channel gateway for PyClaw."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pyclaw.channels.base import BaseChannel

if TYPE_CHECKING:
    from pyclaw.config import PyClawConfig


class DiscordChannel(BaseChannel):
    """Discord bot gateway using discord.py."""

    def __init__(self, config: PyClawConfig):
        super().__init__(config)
        self._client = None
        self._token = os.environ.get(config.channels.discord.token_env, "")

    def start(self) -> None:
        """Start the Discord bot. Blocks."""
        try:
            import discord
        except ImportError:
            raise RuntimeError(
                "discord.py not installed. "
                "Install with: pip install 'pyclaw[discord]'"
            )

        if not self._token:
            raise RuntimeError(
                f"Discord token not set. Set {self.config.channels.discord.token_env} env var."
            )

        intents = discord.Intents.default()
        intents.message_content = True
        self._client = discord.Client(intents=intents)

        @self._client.event
        async def on_ready():
            print(f"PyClaw Discord bot connected as {self._client.user}")

        @self._client.event
        async def on_message(message):
            # Ignore own messages
            if message.author == self._client.user:
                return

            # Only respond to DMs or mentions
            is_dm = isinstance(message.channel, discord.DMChannel)
            is_mentioned = self._client.user in message.mentions

            if not is_dm and not is_mentioned:
                return

            content = message.content
            # Strip mention from content
            if is_mentioned:
                content = content.replace(f"<@{self._client.user.id}>", "").strip()

            if not content:
                return

            user_id = str(message.author.id)
            response = self.handle_incoming(user_id, content)

            # Discord has a 2000 char limit
            if len(response) > 2000:
                for i in range(0, len(response), 2000):
                    await message.reply(response[i : i + 2000])
            else:
                await message.reply(response)

        self._client.run(self._token)

    def stop(self) -> None:
        """Stop the Discord bot."""
        if self._client:
            import asyncio

            asyncio.run(self._client.close())
