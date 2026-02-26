"""PyClaw workspace initialization and management."""

from __future__ import annotations

from pathlib import Path

WORKSPACE_FILES = {
    "IDENTITY.md": """\
# Agent Identity

You are PyClaw, a personal AI assistant.
You are knowledgeable, helpful, and proactive.
You remember past conversations and learn from interactions.
""",
    "SOUL.md": """\
# Core Values & Communication Style

## Values
- Be honest and transparent
- Be helpful without being overbearing
- Respect user privacy
- Admit when you don't know something

## Communication Style
- Concise and clear
- Use markdown formatting when helpful
- Ask clarifying questions when requirements are ambiguous
- Provide actionable suggestions
""",
    "MEMORY.md": """\
# Persistent Memory

This file stores learned knowledge and important facts.
The agent will update this file as it learns new things.

## Facts
(none yet)

## Preferences
(none yet)
""",
    "USER.md": """\
# User Profile

## Name
(not configured)

## Preferences
(not configured)

## Notes
(none yet)
""",
    "HEARTBEAT.md": """\
# Heartbeat Tasks

Periodic background tasks the agent should perform.
Format: one task per line, with optional cron-like schedule.

## Tasks
(none configured)
""",
}


def init_workspace(workspace_path: Path) -> list[Path]:
    """Initialize workspace directory with template .md files.

    Only creates files that don't already exist (won't overwrite).
    Returns list of created file paths.
    """
    workspace_path.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (workspace_path / "sessions").mkdir(exist_ok=True)
    (workspace_path / "data").mkdir(exist_ok=True)

    created = []
    for filename, content in WORKSPACE_FILES.items():
        filepath = workspace_path / filename
        if not filepath.exists():
            filepath.write_text(content, encoding="utf-8")
            created.append(filepath)

    return created
