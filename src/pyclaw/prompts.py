"""PyClaw system prompt templates."""

from __future__ import annotations

SYSTEM_PROMPT_TEMPLATE = """\
You are {agent_name}, a personal AI assistant.

{identity}

{soul}

## User Profile
{user_profile}

## Persistent Memory
{memory}

## Guidelines
- Be helpful, concise, and proactive.
- Use available tools to accomplish tasks (file operations, web search, shell commands).
- Maintain context across the conversation.
- When asked to remember something, note that it should be saved to memory files.

## Workspace
Your workspace is at: {workspace_path}
You can read and write files there freely.
"""


def build_system_prompt(
    *,
    agent_name: str = "PyClaw",
    identity: str = "",
    soul: str = "",
    user_profile: str = "",
    memory: str = "",
    workspace_path: str = "",
) -> str:
    """Build the system prompt with workspace context injected."""
    return SYSTEM_PROMPT_TEMPLATE.format(
        agent_name=agent_name,
        identity=identity or "A capable personal AI assistant.",
        soul=soul or "Be helpful, honest, and harmless.",
        user_profile=user_profile or "No user profile configured yet.",
        memory=memory or "No persistent memories yet.",
        workspace_path=workspace_path,
    )
