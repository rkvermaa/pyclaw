"""Telegram channel gateway for PyClaw."""

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING

from pyclaw.channels.base import BaseChannel

if TYPE_CHECKING:
    from pyclaw.config import PyClawConfig


class TelegramChannel(BaseChannel):
    """Telegram bot gateway using python-telegram-bot."""

    def __init__(self, config: PyClawConfig):
        super().__init__(config)
        self._application = None
        tg_config = config.channels.telegram
        self._token = os.environ.get(tg_config.token_env, "")
        self._allowed_users = tg_config.allowed_users

    def start(self) -> None:
        """Start the Telegram bot. Blocks."""
        try:
            from telegram import Update
            from telegram.ext import (
                ApplicationBuilder,
                CommandHandler,
                MessageHandler,
                filters,
            )
        except ImportError:
            raise RuntimeError(
                "python-telegram-bot not installed. "
                "Install with: pip install 'pyclaw[telegram]'"
            )

        if not self._token:
            raise RuntimeError(
                f"Telegram token not set. Set {self.config.channels.telegram.token_env} env var."
            )

        async def handle_message(update: Update, context):
            if not update.message or not update.message.text:
                return

            user_id = str(update.message.from_user.id)

            # Check allowed users if configured
            if self._allowed_users and int(user_id) not in self._allowed_users:
                await update.message.reply_text("Unauthorized.")
                return

            response = await asyncio.to_thread(
                self.handle_incoming, user_id, update.message.text
            )
            await update.message.reply_text(response)

        async def handle_start(update: Update, context):
            await update.message.reply_text(
                "Hello! I'm PyClaw, your personal AI assistant. Send me a message!"
            )

        self._application = (
            ApplicationBuilder()
            .token(self._token)
            .build()
        )
        self._application.add_handler(CommandHandler("start", handle_start))
        self._application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        )
        self._application.run_polling()

    def stop(self) -> None:
        """Stop the Telegram bot."""
        if self._application:
            self._application.stop()
