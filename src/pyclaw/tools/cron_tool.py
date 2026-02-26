"""HEARTBEAT.md management tool for the agent."""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool


def build_cron_tools(workspace_path: Path) -> list:
    """Build heartbeat/cron management tools."""

    @tool
    def add_heartbeat_task(task: str) -> str:
        """Add a periodic task to HEARTBEAT.md.

        Args:
            task: Description of the task to run periodically.

        Returns:
            Confirmation message.
        """
        heartbeat_path = workspace_path / "HEARTBEAT.md"
        if not heartbeat_path.exists():
            return "Error: HEARTBEAT.md not found. Run 'pyclaw onboard' first."

        content = heartbeat_path.read_text(encoding="utf-8")

        # Find the ## Tasks section and append
        if "(none configured)" in content:
            content = content.replace("(none configured)", f"- {task}")
        else:
            content = content.rstrip() + f"\n- {task}\n"

        heartbeat_path.write_text(content, encoding="utf-8")
        return f"Added heartbeat task: {task}"

    @tool
    def list_heartbeat_tasks() -> str:
        """List all periodic tasks from HEARTBEAT.md.

        Returns:
            List of configured heartbeat tasks.
        """
        from pyclaw.heartbeat.scheduler import parse_heartbeat_file

        tasks = parse_heartbeat_file(workspace_path)
        if not tasks:
            return "No heartbeat tasks configured."
        return "Heartbeat tasks:\n" + "\n".join(f"- {t}" for t in tasks)

    @tool
    def remove_heartbeat_task(task: str) -> str:
        """Remove a periodic task from HEARTBEAT.md.

        Args:
            task: The exact task text to remove.

        Returns:
            Confirmation message.
        """
        heartbeat_path = workspace_path / "HEARTBEAT.md"
        if not heartbeat_path.exists():
            return "Error: HEARTBEAT.md not found."

        content = heartbeat_path.read_text(encoding="utf-8")
        line_to_remove = f"- {task}"

        if line_to_remove not in content:
            return f"Task not found: {task}"

        content = content.replace(line_to_remove + "\n", "")
        content = content.replace(line_to_remove, "")

        # If no tasks remain, add placeholder
        from pyclaw.heartbeat.scheduler import parse_heartbeat_file

        heartbeat_path.write_text(content, encoding="utf-8")
        remaining = parse_heartbeat_file(workspace_path)
        if not remaining:
            content = heartbeat_path.read_text(encoding="utf-8")
            if "## Tasks" in content and "(none configured)" not in content:
                content = content.replace("## Tasks", "## Tasks\n(none configured)")
                heartbeat_path.write_text(content, encoding="utf-8")

        return f"Removed heartbeat task: {task}"

    return [add_heartbeat_task, list_heartbeat_tasks, remove_heartbeat_task]
