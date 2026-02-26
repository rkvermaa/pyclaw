"""Load workspace .md files as memory sources for the agent."""

from __future__ import annotations

from pathlib import Path


def load_workspace_memory(workspace_path: Path) -> dict[str, str]:
    """Load all .md files from workspace into a dict.

    Returns a mapping of filename -> content for files that exist.
    """
    memory: dict[str, str] = {}
    md_files = ["IDENTITY.md", "SOUL.md", "MEMORY.md", "USER.md", "HEARTBEAT.md"]

    for filename in md_files:
        filepath = workspace_path / filename
        if filepath.exists():
            memory[filename] = filepath.read_text(encoding="utf-8")

    return memory
