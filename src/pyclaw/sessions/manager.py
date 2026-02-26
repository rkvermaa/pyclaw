"""Session and thread_id management for PyClaw."""

from __future__ import annotations

import uuid
from pathlib import Path


def get_default_thread_id() -> str:
    """Return the default interactive session thread ID."""
    return "pyclaw-interactive"


def new_thread_id() -> str:
    """Generate a new unique thread ID."""
    return f"pyclaw-{uuid.uuid4().hex[:12]}"


def get_channel_thread_id(channel: str, user_id: str) -> str:
    """Get a thread ID for a specific channel + user combination."""
    return f"pyclaw-{channel}-{user_id}"


def get_checkpointer_path(workspace_path: Path) -> Path:
    """Return the path to the SQLite checkpointer database."""
    sessions_dir = workspace_path / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir / "checkpoints.sqlite"
