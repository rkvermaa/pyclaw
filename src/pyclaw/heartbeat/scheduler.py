"""APScheduler-based heartbeat runner for PyClaw."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyclaw.config import PyClawConfig


def parse_heartbeat_file(workspace_path: Path) -> list[str]:
    """Parse HEARTBEAT.md and return a list of task descriptions."""
    heartbeat_path = workspace_path / "HEARTBEAT.md"
    if not heartbeat_path.exists():
        return []

    content = heartbeat_path.read_text(encoding="utf-8")
    tasks = []

    in_tasks_section = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## Tasks"):
            in_tasks_section = True
            continue
        if in_tasks_section and stripped.startswith("## "):
            break
        if in_tasks_section and stripped.startswith("- "):
            task_text = stripped[2:].strip()
            if task_text and task_text != "(none configured)":
                tasks.append(task_text)

    return tasks


def list_heartbeat_tasks(workspace_path: Path) -> list[str]:
    """List all heartbeat tasks from HEARTBEAT.md."""
    return parse_heartbeat_file(workspace_path)


def _execute_heartbeat(config: PyClawConfig):
    """Execute one heartbeat cycle: run each task through the agent."""
    from pyclaw.agent import create_pyclaw_agent
    from pyclaw.sessions.manager import new_thread_id

    tasks = parse_heartbeat_file(config.workspace_path)
    if not tasks:
        return

    agent, checkpointer = create_pyclaw_agent(config)
    thread_id = new_thread_id()

    for task in tasks:
        prompt = f"[HEARTBEAT] Please perform this periodic task: {task}"
        agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config={"configurable": {"thread_id": thread_id}},
        )


def run_heartbeat(config: PyClawConfig):
    """Start the APScheduler heartbeat loop. Blocks indefinitely."""
    from apscheduler.schedulers.blocking import BlockingScheduler

    scheduler = BlockingScheduler()
    scheduler.add_job(
        _execute_heartbeat,
        "interval",
        minutes=config.heartbeat.interval_minutes,
        args=[config],
        id="pyclaw_heartbeat",
        name="PyClaw Heartbeat",
    )

    # Run once immediately
    _execute_heartbeat(config)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
