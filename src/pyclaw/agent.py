"""Core agent: wraps create_deep_agent() with PyClaw configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.sqlite import SqliteSaver

from pyclaw.memory.loader import load_workspace_memory
from pyclaw.prompts import build_system_prompt
from pyclaw.sessions.manager import get_checkpointer_path
from pyclaw.tools import build_tools

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph

    from pyclaw.config import PyClawConfig


def create_pyclaw_agent(config: PyClawConfig) -> tuple[CompiledStateGraph, SqliteSaver]:
    """Create a configured PyClaw agent.

    Returns a tuple of (agent, checkpointer) so the caller can manage
    the checkpointer lifecycle.
    """
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
