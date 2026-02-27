"""Abstract base class for PyClaw channel gateways."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyclaw.config import PyClawConfig


class BaseChannel(ABC):
    """Base class for all channel gateways (Telegram, Discord, Slack)."""

    def __init__(self, config: PyClawConfig):
        self.config = config

        from pyclaw.agent import create_pyclaw_agent

        self._agent, self._checkpointer = create_pyclaw_agent(config)

    @abstractmethod
    def start(self) -> None:
        """Start the channel gateway. This should block."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop the channel gateway gracefully."""
        ...

    def handle_incoming(self, user_id: str, message: str) -> str:
        """Process an incoming message through the PyClaw agent.

        Returns the agent's response text.
        """
        from pyclaw.sessions.manager import get_channel_thread_id

        channel_name = self.__class__.__name__.replace("Channel", "").lower()
        thread_id = get_channel_thread_id(channel_name, user_id)

        result = self._agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config={"configurable": {"thread_id": thread_id}},
        )

        messages = result.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "type") and msg.type == "ai" and msg.content:
                return msg.content

        return "I couldn't generate a response."
