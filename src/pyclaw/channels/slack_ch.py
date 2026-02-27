"""Slack channel gateway for PyClaw."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pyclaw.channels.base import BaseChannel

if TYPE_CHECKING:
    from pyclaw.config import PyClawConfig


class SlackChannel(BaseChannel):
    """Slack bot gateway using slack-bolt."""

    def __init__(self, config: PyClawConfig):
        super().__init__(config)
        self._app = None
        self._handler = None
        self._token = os.environ.get(config.channels.slack.token_env, "")

    def start(self) -> None:
        """Start the Slack bot. Blocks."""
        try:
            from slack_bolt import App
            from slack_bolt.adapter.socket_mode import SocketModeHandler
        except ImportError:
            raise RuntimeError(
                "slack-bolt not installed. "
                "Install with: pip install 'pyclaw[slack]'"
            )

        if not self._token:
            raise RuntimeError(
                f"Slack token not set. Set {self.config.channels.slack.token_env} env var."
            )

        app_token = os.environ.get("SLACK_APP_TOKEN", "")
        if not app_token:
            raise RuntimeError("SLACK_APP_TOKEN environment variable not set.")

        self._app = App(token=self._token)

        @self._app.event("app_mention")
        def handle_mention(event, say):
            user_id = event.get("user", "unknown")
            text = event.get("text", "")
            # Strip the bot mention from text
            text = text.split(">", 1)[-1].strip() if ">" in text else text
            if text:
                response = self.handle_incoming(user_id, text)
                say(response)

        @self._app.event("message")
        def handle_dm(event, say):
            # Only handle DMs (channel_type == "im")
            if event.get("channel_type") != "im":
                return
            # Ignore bot messages
            if event.get("bot_id"):
                return

            user_id = event.get("user", "unknown")
            text = event.get("text", "")
            if text:
                response = self.handle_incoming(user_id, text)
                say(response)

        self._handler = SocketModeHandler(self._app, app_token)
        self._handler.start()

    def stop(self) -> None:
        """Stop the Slack bot."""
        if self._handler:
            self._handler.close()
