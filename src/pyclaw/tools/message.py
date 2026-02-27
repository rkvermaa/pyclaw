"""Cross-channel messaging tool for the agent."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from langchain_core.tools import tool

if TYPE_CHECKING:
    from pyclaw.config import PyClawConfig


def _run_async(coro):
    """Run a coroutine, handling the case where an event loop is already running."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()


def build_message_tool(config: PyClawConfig):
    """Build a cross-channel message sending tool."""

    @tool
    def send_message(channel: str, user_id: str, message: str) -> str:
        """Send a message to a user on a specific channel.

        Args:
            channel: The channel to send on ('telegram', 'discord', 'slack').
            user_id: The user/channel ID to send to.
            message: The message text to send.

        Returns:
            Confirmation or error message.
        """
        import os

        channel = channel.lower()

        if channel == "telegram":
            if not config.channels.telegram.enabled:
                return "Telegram channel is not enabled."
            try:
                import telegram

                token = os.environ.get(config.channels.telegram.token_env, "")
                if not token:
                    return f"Telegram token not set ({config.channels.telegram.token_env})."
                bot = telegram.Bot(token=token)
                _run_async(bot.send_message(chat_id=user_id, text=message))
                return f"Message sent to Telegram user {user_id}."
            except ImportError:
                return "python-telegram-bot not installed."
            except Exception as e:
                return f"Error sending Telegram message: {e}"

        elif channel == "discord":
            return "Discord message sending requires an active bot connection. Use the gateway."

        elif channel == "slack":
            if not config.channels.slack.enabled:
                return "Slack channel is not enabled."
            try:
                from slack_sdk import WebClient

                token = os.environ.get(config.channels.slack.token_env, "")
                if not token:
                    return f"Slack token not set ({config.channels.slack.token_env})."
                client = WebClient(token=token)
                client.chat_postMessage(channel=user_id, text=message)
                return f"Message sent to Slack channel/user {user_id}."
            except ImportError:
                return "slack-bolt not installed."
            except Exception as e:
                return f"Error sending Slack message: {e}"

        else:
            return f"Unknown channel: {channel}. Use 'telegram', 'discord', or 'slack'."

    return send_message
