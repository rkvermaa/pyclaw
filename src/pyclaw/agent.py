"""Core agent: wraps create_deep_agent() with PyClaw configuration."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.sqlite import SqliteSaver

from pyclaw.config import DEFAULT_ENV_PATH
from pyclaw.memory.loader import load_workspace_memory
from pyclaw.prompts import build_system_prompt
from pyclaw.sessions.manager import get_checkpointer_path
from pyclaw.tools import build_tools

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph

    from pyclaw.config import PyClawConfig


def _load_env_file(path: os.PathLike) -> None:
    """Load key=value pairs from a file into os.environ (no extra dependency)."""
    env_path = type(path)(path) if not hasattr(path, "exists") else path
    from pathlib import Path

    env_path = Path(env_path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        if key:
            os.environ.setdefault(key, value)


def create_pyclaw_agent(config: PyClawConfig) -> tuple[CompiledStateGraph, SqliteSaver]:
    """Create a configured PyClaw agent.

    Returns a tuple of (agent, checkpointer) so the caller can manage
    the checkpointer lifecycle.
    """
    # Load env vars from ~/.pyclaw/.env (API keys, etc.)
    _load_env_file(DEFAULT_ENV_PATH)

    # Initialize the LLM
    model = init_chat_model(config.default_model)

    # Build custom tools
    custom_tools = build_tools(config)

    # Set up workspace backend
    workspace_path = config.workspace_path
    workspace_path.mkdir(parents=True, exist_ok=True)

    backend = LocalShellBackend(root_dir=str(workspace_path))

    # Load workspace memory files for the system prompt
    memory_files = load_workspace_memory(workspace_path)

    system_prompt = build_system_prompt(
        identity=memory_files.get("IDENTITY.md", ""),
        soul=memory_files.get("SOUL.md", ""),
        user_profile=memory_files.get("USER.md", ""),
        memory=memory_files.get("MEMORY.md", ""),
        workspace_path=str(workspace_path),
    )

    # Set up SQLite checkpointer for session persistence
    db_path = get_checkpointer_path(workspace_path)
    checkpointer = SqliteSaver(str(db_path))

    # Create the deep agent
    agent = create_deep_agent(
        model=model,
        tools=custom_tools or None,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        backend=backend,
        name="pyclaw",
    )

    return agent, checkpointer
